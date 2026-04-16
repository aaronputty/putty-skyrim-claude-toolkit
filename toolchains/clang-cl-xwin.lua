-- toolchains/clang-cl-xwin.lua
--
-- Reusable xmake toolchain for cross-compiling Windows PE/COFF binaries
-- (SKSE plugins, DLLs, etc.) from the Linux dev container.
--
-- Requires:
--   - clang-cl and lld-link on PATH (installed via Dockerfile)
--   - xwin SDK splat at XWIN_DIR (default: /opt/xwin)
--
-- Usage in a mod's xmake.lua:
--   includes("path/to/toolchains/clang-cl-xwin.lua")
--   set_toolchains("clang-cl-xwin")
--   set_plat("windows")
--   set_arch("x64")

toolchain("clang-cl-xwin")
    set_kind("standalone")
    set_toolset("cc",  "clang-cl")
    set_toolset("cxx", "clang-cl")
    set_toolset("ld",  "lld-link")
    set_toolset("ar",  "llvm-lib")

    on_load(function(toolchain)
        local xwin = os.getenv("XWIN_DIR") or "/opt/xwin"

        -- Windows SDK + MSVC CRT headers (treated as system includes to suppress
        -- warnings from Microsoft headers we don't own)
        toolchain:add("sysincludedirs",
            path.join(xwin, "crt/include"),
            path.join(xwin, "sdk/include/ucrt"),
            path.join(xwin, "sdk/include/um"),
            path.join(xwin, "sdk/include/shared"))

        -- Windows SDK + MSVC CRT import libs
        toolchain:add("linkdirs",
            path.join(xwin, "crt/lib/x86_64"),
            path.join(xwin, "sdk/lib/um/x86_64"))

        -- Target Windows x64 PE/COFF
        toolchain:add("cxflags", "--target=x86_64-pc-windows-msvc")
        toolchain:add("ldflags", "/machine:x64")
    end)
