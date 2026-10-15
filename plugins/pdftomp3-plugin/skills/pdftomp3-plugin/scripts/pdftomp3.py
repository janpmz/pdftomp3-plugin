#!/usr/bin/env python3
"""Call PDFTOMP3-Plugin without an MCP connection."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import webbrowser

ACTIONS = {
    "speech-setup": "speech-setup", "voices": "voices",
    "begin": "documents/begin", "chapter": "documents/chapter",
    "finish": "documents/finish", "get": "documents/get",
    "list": "documents/list", "audio": "documents/audio", "send": "passages",
}


class PlayerError(Exception):
    def __init__(self, message, code="CLIENT_ERROR", details=None, status=None):
        super().__init__(message)
        self.code, self.details, self.status = code, details or {}, status

    def result(self):
        return {**self.details, "code": self.code, "message": str(self)}


def api_base(value):
    parts = urlsplit(value)
    local = parts.hostname in ("localhost", "127.0.0.1", "::1")
    try:
        port = parts.port
    except ValueError:
        raise PlayerError("Use a valid server address.") from None
    if (not parts.hostname or parts.username or parts.password or parts.query or parts.fragment
            or parts.path not in ("", "/") or (parts.scheme != "https" and not (parts.scheme == "http" and local))
            or port == 0):
        raise PlayerError("Use HTTPS, or HTTP on localhost, with no path or sign-in details.")
    return value.rstrip("/") + "/"


def configured_api():
    try:
        value = json.loads(Path(__file__).with_name("server.json").read_text(encoding="utf-8"))["api_url"]
        if not isinstance(value, str):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise PlayerError("Could not read the plugin's server address. Reinstall the plugin.", "BAD_CONFIG") from None
    return api_base(value)


def data_folder():
    override = os.environ.get("PDFTOMP3_DATA_DIR") or os.environ.get("DOCUMENT_PLAYER_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        root, old_name = Path.home() / "Library" / "Application Support", "Document Player"
    elif os.name == "nt":
        root, old_name = Path(os.environ.get("LOCALAPPDATA", Path.home())), "Document Player"
    else:
        root, old_name = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")), "document-player"
    folder = root / ("pdftomp3" if os.name != "nt" and sys.platform != "darwin" else "PDFTOMP3")
    legacy = root / old_name
    # Reuse an older install's sign-in without copying or moving its tokens.
    return legacy if not folder.exists() and legacy.is_dir() else folder


def windows_user_only(path, directory=False):
    """Replace Windows access rules with one grant for the current user."""
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    pointer = ctypes.c_void_p

    def bind(library, name, result, *arguments):
        function = getattr(library, name)
        function.restype, function.argtypes = result, arguments
        return function

    current_process = bind(kernel, "GetCurrentProcess", wintypes.HANDLE)
    close_handle = bind(kernel, "CloseHandle", wintypes.BOOL, wintypes.HANDLE)
    free = bind(kernel, "LocalFree", pointer, pointer)
    open_token = bind(security, "OpenProcessToken", wintypes.BOOL,
                      wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
    token_info = bind(security, "GetTokenInformation", wintypes.BOOL,
                      wintypes.HANDLE, ctypes.c_int, pointer, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
    sid_string = bind(security, "ConvertSidToStringSidW", wintypes.BOOL,
                      pointer, ctypes.POINTER(wintypes.LPWSTR))
    from_string = bind(security, "ConvertStringSecurityDescriptorToSecurityDescriptorW", wintypes.BOOL,
                       wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(pointer), ctypes.POINTER(wintypes.DWORD))
    get_dacl = bind(security, "GetSecurityDescriptorDacl", wintypes.BOOL,
                    pointer, ctypes.POINTER(wintypes.BOOL), ctypes.POINTER(pointer), ctypes.POINTER(wintypes.BOOL))
    set_access = bind(security, "SetNamedSecurityInfoW", wintypes.DWORD,
                      wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD, pointer, pointer, pointer, pointer)

    class TokenUser(ctypes.Structure):
        _fields_ = [("sid", pointer), ("attributes", wintypes.DWORD)]

    token, descriptor, user_text = wintypes.HANDLE(), pointer(), wintypes.LPWSTR()
    try:
        # TOKEN_QUERY; TokenUser. Read the process token, not a supplied user name.
        if not open_token(current_process(), 0x0008, ctypes.byref(token)):
            raise ctypes.WinError(ctypes.get_last_error())
        size = wintypes.DWORD()
        token_info(token, 1, None, 0, ctypes.byref(size))
        if ctypes.get_last_error() != 122:  # ERROR_INSUFFICIENT_BUFFER
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_string_buffer(size.value)
        if not token_info(token, 1, buffer, size, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        user = ctypes.cast(buffer, ctypes.POINTER(TokenUser)).contents.sid
        if not sid_string(user, ctypes.byref(user_text)):
            raise ctypes.WinError(ctypes.get_last_error())
        # P blocks inherited grants. OI/CI pass this user's grant to child files/folders.
        flags = "OICI" if directory else ""
        rules = f"D:P(A;{flags};FA;;;{user_text.value})"
        if not from_string(rules, 1, ctypes.byref(descriptor), None):
            raise ctypes.WinError(ctypes.get_last_error())
        present, defaulted, dacl = wintypes.BOOL(), wintypes.BOOL(), pointer()
        if not get_dacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not present.value or not dacl.value:
            raise OSError("Windows did not return file access rules.")
        # SE_FILE_OBJECT; OWNER + DACL + PROTECTED_DACL_SECURITY_INFORMATION.
        result = set_access(str(path.resolve()), 1, 0x80000005, user, None, dacl, None)
        if result:
            raise ctypes.WinError(result)
    finally:
        if user_text:
            free(ctypes.cast(user_text, pointer))
        if descriptor:
            free(descriptor)
        if token:
            close_handle(token)


def restrict_access(path, directory=False, fd=None):
    if os.name == "nt":
        windows_user_only(path, directory)
    elif fd is not None:
        os.fchmod(fd, 0o700 if directory else 0o600)
    else:
        path.chmod(0o700 if directory else 0o600)


def prepare_data_folder(folder):
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    restrict_access(folder, directory=True)


class CredentialStore:
    def __init__(self, base, folder=None):
        self.folder = Path(folder) if folder is not None else data_folder()
        self.path = self.folder / ("sign-in-" + hashlib.sha256(api_base(base).encode()).hexdigest() + ".json")

    def read(self):
        try:
            prepare_data_folder(self.folder)
            with self.path.open(encoding="utf-8") as handle:
                restrict_access(self.path, fd=handle.fileno())
                return json.load(handle)
        except FileNotFoundError:
            return None
        except (ValueError, UnicodeError):
            self.clear()
            return None
        except OSError:
            raise PlayerError("Could not read the local sign-in file. Check access to your data folder.", "STORAGE_UNAVAILABLE") from None

    def write(self, value):
        temporary = None
        try:
            prepare_data_folder(self.folder)
            fd, name = tempfile.mkstemp(prefix=self.path.stem + "-", suffix=".tmp", dir=self.folder)
            temporary = Path(name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                restrict_access(temporary, fd=handle.fileno())
                json.dump(value, handle, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError:
            raise PlayerError("Could not save the local sign-in file. Check access to your data folder.", "STORAGE_UNAVAILABLE") from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def clear(self):
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            raise PlayerError("Could not remove the local sign-in file.", "STORAGE_UNAVAILABLE") from None


@contextmanager
def session_lock(folder, base):
    """Keep two helper calls from renewing the same sign-in at once."""
    prepare_data_folder(folder)
    lock_path = folder / (hashlib.sha256(base.encode()).hexdigest() + ".lock")
    with open(lock_path, "a+b") as handle:
        restrict_access(lock_path, fd=handle.fileno())
        if os.name == "nt":
            import msvcrt
            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, body=None, bearer=None, form=False):
    headers = {"Accept": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    data = None
    if body is not None:
        data = (urlencode(body) if form else json.dumps(body, ensure_ascii=False)).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
    try:
        with build_opener(NoRedirects()).open(Request(url, data=data, headers=headers), timeout=45) as reply:
            result = json.loads(reply.read(2_000_001))
            if not isinstance(result, dict):
                raise ValueError()
            return result
    except HTTPError as error:
        try:
            result = json.loads(error.read(100_000))
            if not isinstance(result, dict):
                result = {}
        except (ValueError, UnicodeError):
            result = {}
        finally:
            error.close()
        message = result.get("message") or result.get("error_description") or result.get("error")
        if not isinstance(message, str):
            message = "PDFTOMP3 could not complete this request."
        details = {key: result[key] for key in ("issues", "hint", "needs_setup", "settings_url") if key in result}
        raise PlayerError(message, result.get("code", "HTTP_ERROR"), details, error.code) from None
    except (URLError, TimeoutError, OSError):
        raise PlayerError("Could not reach PDFTOMP3. Check the connection and try again.", "NETWORK_ERROR") from None
    except (ValueError, UnicodeError):
        raise PlayerError("PDFTOMP3 returned an unreadable reply.", "BAD_REPLY") from None


class Client:
    def __init__(self, base, store, request=request_json, clock=time.time):
        self.base, self.store, self.request, self.clock = api_base(base), store, request, clock

    def info(self):
        data = self.request(self.base + "agent-api/info")
        expected = {
            "api_url": "agent-api/", "resource": "mcp", "issuer": "mcp/oauth",
            "authorization_endpoint": "mcp/oauth/authorize", "token_endpoint": "mcp/oauth/token",
            "registration_endpoint": "mcp/oauth/register", "revocation_endpoint": "mcp/oauth/revoke",
        }
        if any(data.get(key) != self.base + path for key, path in expected.items()):
            raise PlayerError("The server's sign-in addresses do not match this server.", "BAD_REPLY")
        scopes = data.get("scopes")
        if (not isinstance(scopes, list) or not scopes
                or not all(isinstance(scope, str) and scope and not any(c.isspace() for c in scope) for scope in scopes)):
            raise PlayerError("The server did not return valid sign-in permissions.", "BAD_REPLY")
        return data

    def save_tokens(self, data, info, client_id):
        if (not isinstance(data.get("access_token"), str) or not data["access_token"]
                or not isinstance(data.get("refresh_token"), str) or not data["refresh_token"]
                or data.get("token_type", "").lower() != "bearer"
                or not isinstance(data.get("expires_in"), (int, float)) or data["expires_in"] <= 0):
            raise PlayerError("The server returned an incomplete sign-in.", "BAD_REPLY")
        state = {"access_token": data["access_token"], "refresh_token": data["refresh_token"],
                 "expires_at": self.clock() + data["expires_in"], "client_id": client_id,
                 "base": self.base, "info": info}
        self.store.write(state)
        return state

    def refresh(self, state):
        try:
            data = self.request(self.base + "mcp/oauth/token", {
                "grant_type": "refresh_token", "client_id": state["client_id"],
                "refresh_token": state["refresh_token"], "resource": self.base + "mcp",
            }, form=True)
        except PlayerError as error:
            if error.status in (400, 401):
                self.store.clear()
                raise PlayerError("This connection has ended. Run login to connect again.", "SIGN_IN_REQUIRED") from None
            raise
        return self.save_tokens(data, state["info"], state["client_id"])

    def session(self):
        state = self.store.read()
        if (not isinstance(state, dict) or state.get("base") != self.base
                or not isinstance(state.get("expires_at"), (int, float))
                or not all(isinstance(state.get(key), str) and state[key] for key in ("access_token", "refresh_token", "client_id"))
                or not isinstance(state.get("info"), dict)):
            if state is not None:
                self.store.clear()
            raise PlayerError("Run login to connect your PDFTOMP3 account.", "SIGN_IN_REQUIRED")
        if state["expires_at"] <= self.clock() + 45:
            state = self.refresh(state)
        return state

    def call(self, action, body=None):
        if action not in ACTIONS:
            raise PlayerError("Choose a supported action.")
        state = self.session()
        try:
            return self.request(self.base + "agent-api/" + ACTIONS[action], body or {}, bearer=state["access_token"])
        except PlayerError as error:
            if error.status != 401:
                raise
        state = self.refresh(state)
        try:
            return self.request(self.base + "agent-api/" + ACTIONS[action], body or {}, bearer=state["access_token"])
        except PlayerError as error:
            if error.status == 401:
                self.store.clear()
                raise PlayerError("Run login to connect again.", "SIGN_IN_REQUIRED") from None
            raise

    def login(self, emit, open_browser=webbrowser.open, timeout=600):
        info = self.info()
        scope = " ".join(info["scopes"])
        if self.store.read():
            return self.status()
        verifier, state = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        result = {}

        class Callback(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                address = urlsplit(self.path)
                query = parse_qs(address.query)
                valid = (address.path == "/callback" and len(query.get("state", [])) == 1
                         and secrets.compare_digest(query["state"][0], state)
                         and query.get("iss") == [info["issuer"]])
                if not valid:
                    self.send_error(400, "This sign-in does not match. Return to Codex.")
                    return
                if len(query.get("code", [])) == 1 and "error" not in query:
                    result["code"] = query["code"][0]
                else:
                    result["denied"] = True
                body = b"Sign-in received. You can return to Codex."
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        with HTTPServer(("127.0.0.1", 0), Callback) as server:
            server.timeout = 1
            redirect = f"http://127.0.0.1:{server.server_port}/callback"
            registration = self.request(info["registration_endpoint"], {
                "client_name": "PDFTOMP3-Plugin", "redirect_uris": [redirect],
                "token_endpoint_auth_method": "none",
                "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"],
                "scope": scope,
            })
            client_id = registration.get("client_id")
            if not isinstance(client_id, str) or not client_id:
                raise PlayerError("Could not start sign-in.", "BAD_REPLY")
            address = info["authorization_endpoint"] + "?" + urlencode({
                "response_type": "code", "client_id": client_id, "redirect_uri": redirect,
                "code_challenge": challenge, "code_challenge_method": "S256", "state": state,
                "scope": scope, "resource": info["resource"],
            })
            emit({"status": "sign_in_required", "url": address,
                  "message": "Open this link, sign in, and choose Connect. Leave this helper running."})
            try:
                open_browser(address)
            except Exception:
                pass
            end = time.monotonic() + timeout
            while not result and time.monotonic() < end:
                server.handle_request()
            if not result:
                raise PlayerError("Sign-in timed out. Run login to try again.", "SIGN_IN_TIMEOUT")
            if result.get("denied"):
                raise PlayerError("You cancelled the connection.", "SIGN_IN_CANCELLED")
            tokens = self.request(info["token_endpoint"], {
                "grant_type": "authorization_code", "client_id": client_id, "code": result["code"],
                "code_verifier": verifier, "redirect_uri": redirect, "resource": info["resource"],
            }, form=True)
            self.save_tokens(tokens, info, client_id)
        return self.status()

    def status(self):
        if not self.store.read():
            return {"status": "signed_out", "connected": False, "message": "Run login to connect."}
        setup = self.call("speech-setup")
        return {**setup, "speech_status": setup.get("status"), "status": "connected", "connected": True}

    def logout(self):
        state = self.store.read()
        if state:
            # Clear locally only after the server confirms revocation.
            self.request(self.base + "mcp/oauth/revoke", {
                "client_id": state["client_id"], "token": state["refresh_token"],
                "token_type_hint": "refresh_token",
            }, form=True)
            self.store.clear()
        return {"status": "disconnected"}


def output(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def parser():
    result = argparse.ArgumentParser(description="PDFTOMP3-Plugin: send text and prepared chapters to PDF TO MP3.")
    result.add_argument("--api-url", default=os.environ.get("PDFTOMP3_API_URL") or os.environ.get("DOCUMENT_PLAYER_API_URL"))
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("install", help="Prepare the local sign-in folder. No packages are needed.")
    login = commands.add_parser("login", help="Connect through browser sign-in.")
    login.add_argument("--no-browser", action="store_true", help="Show the sign-in link without opening it.")
    commands.add_parser("status", help="Check account access and speech setup.")
    commands.add_parser("logout", help="Revoke the connection and remove the saved sign-in.")
    for name in ACTIONS:
        action = commands.add_parser(name)
        action.add_argument("--input", help="Read the request from a JSON file, or - for standard input.")
        if name in ("get", "finish", "audio", "voices"):
            action.add_argument("--document-id")
        if name == "get":
            action.add_argument("--chapter-index", type=int)
        if name == "audio":
            action.add_argument("--paid-audio", action="store_true", help="The user requested paid speech.")
    return result


def run(args, client):
    if args.command == "login":
        return client.login(output, open_browser=(lambda _url: None) if args.no_browser else webbrowser.open)
    if args.command == "status":
        return client.status()
    if args.command == "logout":
        return client.logout()
    body = {}
    if args.input:
        try:
            if args.input == "-":
                body = json.load(sys.stdin)
            else:
                body = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (ValueError, OSError, UnicodeError):
            raise PlayerError("Use a readable JSON request file.", "BAD_INPUT") from None
        if not isinstance(body, dict):
            raise PlayerError("The request file must hold one JSON object.", "BAD_INPUT")
    if getattr(args, "document_id", None):
        body["document_id"] = args.document_id
    if getattr(args, "chapter_index", None) is not None:
        body["chapter_index"] = args.chapter_index
    if args.command == "audio" and not args.paid_audio:
        raise PlayerError("Use --paid-audio only when the user asked for speech.", "AUDIO_NOT_REQUESTED")
    return client.call(args.command, body)


def main():
    args = parser().parse_args()
    folder = data_folder()
    try:
        base = api_base(args.api_url) if args.api_url else configured_api()
        store = CredentialStore(base, folder)
        if args.command == "install":
            prepare_data_folder(folder)
            output({"status": "installed", "api_url": base, "sign_in_file": str(store.path),
                    "message": "The helper is ready. Run login to connect your account."})
            return 0
        with session_lock(folder, base):
            output(run(args, Client(base, store)))
        return 0
    except PlayerError as error:
        output(error.result())
        return 1
    except KeyboardInterrupt:
        output({"code": "CANCELLED", "message": "Stopped."})
        return 130
    except OSError:
        output({"code": "STORAGE_UNAVAILABLE", "message": "Could not open the local sign-in folder. Check access to your data folder."})
        return 1
    except Exception:
        output({"code": "CLIENT_ERROR", "message": "The helper could not finish. Check your saved connection and try again."})
        return 1


if __name__ == "__main__":
    sys.exit(main())
