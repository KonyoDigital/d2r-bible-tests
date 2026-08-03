#include <CascLib.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
int main(int argc, char** argv){
  if (argc < 3){ fprintf(stderr, "usage: casc_extract <storage> --list|<file> [out]\n"); return 2; }
  HANDLE hs = NULL;
  if (!CascOpenStorage(argv[1], 0, &hs)){ fprintf(stderr, "open storage failed %u\n", GetCascError()); return 1; }
  if (!strcmp(argv[2], "--list")){
    CASC_FIND_DATA fd; HANDLE hf = CascFindFirstFile(hs, "*", &fd, NULL);
    if (hf == NULL){ fprintf(stderr, "find failed %u\n", GetCascError()); CascCloseStorage(hs); return 1; }
    long n = 0;
    do { printf("%s\n", fd.szFileName); n++; } while (CascFindNextFile(hf, &fd));
    CascFindClose(hf); fprintf(stderr, "%ld files\n", n); CascCloseStorage(hs); return 0;
  }
  HANDLE hf = NULL;
  if (!CascOpenFile(hs, argv[2], 0, CASC_OPEN_BY_NAME, &hf)){
    fprintf(stderr, "open file failed %u\n", GetCascError()); CascCloseStorage(hs); return 1; }
  FILE* out = (argc > 3) ? fopen(argv[3], "wb") : stdout;
  char buf[65536]; DWORD got = 0;
  while (CascReadFile(hf, buf, sizeof(buf), &got) && got > 0) fwrite(buf, 1, got, out);
  if (out != stdout) fclose(out);
  CascCloseFile(hf); CascCloseStorage(hs); return 0;
}
