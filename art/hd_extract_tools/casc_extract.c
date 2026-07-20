// casc_extract.c — minimal CASC file puller for D2R local install.
// Usage:
//   casc_extract <d2r_root> <casc_path_with_data:_prefix> <out_file>
//   casc_extract <d2r_root> --enum <substring_filter> <out_listing_file>
#include <CascLib.h>
#include <CascPort.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include <vector>

static bool extractOne(HANDLE hStorage, const char* path, const char* outPath){
    HANDLE hFile = NULL;
    if(!CascOpenFile(hStorage, path, 0, CASC_OPEN_BY_NAME, &hFile)){
        fprintf(stderr, "CascOpenFile failed for %s (err %u)\n", path, GetCascError());
        return false;
    }
    FILE* out = fopen(outPath, "wb");
    if(!out){ fprintf(stderr, "fopen failed for %s\n", outPath); CascCloseFile(hFile); return false; }
    unsigned char buf[65536];
    DWORD read = 0;
    for(;;){
        if(!CascReadFile(hFile, buf, sizeof(buf), &read)) break;
        if(read == 0) break;
        fwrite(buf, 1, read, out);
        if(read < sizeof(buf)) break;
    }
    fclose(out);
    CascCloseFile(hFile);
    return true;
}

static bool enumFiles(HANDLE hStorage, const char* filter, const char* outPath){
    FILE* out = fopen(outPath, "wb");
    if(!out){ fprintf(stderr, "fopen failed for %s\n", outPath); return false; }
    CASC_FIND_DATA cfd;
    HANDLE hFind = CascFindFirstFile(hStorage, "*", &cfd, NULL);
    if(hFind == NULL){ fprintf(stderr, "CascFindFirstFile failed (err %u)\n", GetCascError()); fclose(out); return false; }
    long count = 0;
    do{
        if(!filter || !filter[0] || strstr(cfd.szFileName, filter)){
            fprintf(out, "%s\n", cfd.szFileName);
            count++;
        }
    } while(CascFindNextFile(hFind, &cfd));
    CascFindClose(hFind);
    fclose(out);
    fprintf(stderr, "enumerated %ld matching files\n", count);
    return true;
}

int main(int argc, char** argv){
    if(argc < 4){
        fprintf(stderr, "usage: %s <d2r_root> <path|--enum> <filter_or_out> [out]\n", argv[0]);
        return 1;
    }
    const char* root = argv[1];
    HANDLE hStorage = NULL;
    if(!CascOpenStorage(root, 0, &hStorage)){
        fprintf(stderr, "CascOpenStorage failed for %s (err %u)\n", root, GetCascError());
        return 2;
    }
    bool ok;
    if(strcmp(argv[2], "--enum") == 0){
        ok = enumFiles(hStorage, argv[3], argc > 4 ? argv[4] : "enum_out.txt");
    } else {
        ok = extractOne(hStorage, argv[2], argv[3]);
    }
    CascCloseStorage(hStorage);
    return ok ? 0 : 3;
}
