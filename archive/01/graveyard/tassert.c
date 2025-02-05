#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include "macro.h"
#include "test_framework.h"
#include "tassert.h"

// I searched if there are more obscure path separators. There are!
//
// A lot are from discontinued OSes. Like classic Mac OS (':'), or RISC OS ('.').
// Some others are from very specialized OSes, like Stratus VOS (for fault-tolerant hardware),
// or OpenVMS (ancient OS that predates Linux and Windows, still used as legacy system in some
// industries, like finance, healthcare, manufacturing, ...).
// I will not try to parse this absolutely cursed path from OpenVMS:
//     NODE"accountname password"::device:[directory.subdirectory]filename.type;ver
//
// The only new OS that may be important in the future with an alternative path separator ('>')
// is HarmonyOS and its derivatives, created to circumvent USA's restrictions...
// ... but the only mention of this separator is on Wikipedia, I've found nothing on OpenHarmony's
// source code. It seems weird to me to add a completely new char, it would be such a mess of
// compatibility issues. The user who modified the wiki's page does not have an account, and
// updates a lot of articles related to HarmonyOS. Who are they? Why is it the only place where
// '>' is mentioned? Every filepath I see in every webpage relating to HarmonyOS uses '/'!
// Even the source links for the HarmonyOS shell does not mention '>'!
// So, I will ignore it.
//
// Fun fact: NTFS has a weird feature, "alternate data stream", when a file can have additional
// data accessed only with some software and is defined by the path. For example:
// 'notepad.exe tests.txt' contains some text.
// 'notepad.exe tests:txt:ads.txt' contains some other text.
// 'tests.txt:ads.txt' is not visible in Windows Explorer, and a lot of software don't even know it exists.
// Apparently, it was used for compatibility with other system and to add some metadata from downloaded files.
//
// Another fun Windows fact: the path separator character in Japanese and Korean was displayed as their currency
// sign (Yen an Won), because of their code page before our glorious and blessed golden age of UTF-8.
//
// Anyway, I've looked quickly at some implementations in standard library for the path separator,
// and both in Python (os.path.sep), standard c++ lib (GNU and Windows) (std::path::preferred_separator),
// and Boost they don't try much harder than what's below.
// _WIN32 cover all the use cases that matters (x86, x64, AMD32 and AMD64).
//
// In any case, my goal is just to get the filename from the path given by the '__FILE__' macro, so
// it should be good enough.
const char path_sep =
#ifdef _WIN32
    '\\';
#else
    '/';
#endif

char *get_filename(char *path)
{
    assert(path != NULL);
    char *last_sep = strrchr(path, path_sep);
    assert(last_sep != NULL);
    return last_sep + 1;
}

void tassert(bool success, char *condition, char *message, char *path, char const *func, int line)
{
    assert(condition != NULL);
    assert(message != NULL);
    assert(path != NULL);
    assert(func != NULL);

    char copy[FILENAME_MAX];
    snprintf(copy, ARRAY_LENGTH(copy), "%s", path);
    char *filename = get_filename(copy);

    AssertResult result = {.success = success, .message = {0}};
    int message_length = ARRAY_LENGTH(result.message);
    if (success)
    {
        snprintf(result.message, message_length, "%s -> ok.", condition);
    }
    else
    {
        snprintf(result.message, message_length, "%s -> KO!: %s (%s:%d %s)",
                 condition, message, filename, line, func);
    }
    push_result(result);
}