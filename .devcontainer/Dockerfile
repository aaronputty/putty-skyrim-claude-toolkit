FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Use bash for all RUN commands. Docker defaults to /bin/sh, which breaks the
# xmake install script's profile sourcing step (/bin/sh: xmake: not found).
SHELL ["/bin/bash", "-c"]

# --- Remove Yarn apt source from base image ---
# The base image ships a Yarn repo whose GPG key is expired/missing, causing
# every subsequent apt-get update to fail. We install Node via NodeSource so
# the Yarn repo is not needed.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
          /usr/share/keyrings/yarn.gpg \
    2>/dev/null || true

# --- LLVM 17 (clang-cl + lld-link) ---
# Bullseye's default apt only ships LLVM 13; use the official LLVM apt repo.
RUN curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/llvm.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/llvm.gpg] https://apt.llvm.org/bullseye/ llvm-toolchain-bullseye-17 main" \
        > /etc/apt/sources.list.d/llvm.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        clang-17 \
        lld-17 \
        llvm-17 \
        clang-tools-17 \
        libc++-17-dev \
    && ln -sf /usr/bin/clang-17        /usr/local/bin/clang \
    && ln -sf /usr/bin/clang-cl-17     /usr/local/bin/clang-cl \
    && ln -sf /usr/bin/lld-17          /usr/local/bin/lld \
    && ln -sf /usr/bin/lld-link-17     /usr/local/bin/lld-link \
    && ln -sf /usr/bin/llvm-lib-17     /usr/local/bin/llvm-lib \
    && ln -sf /usr/bin/llvm-ar-17      /usr/local/bin/llvm-ar \
    && rm -rf /var/lib/apt/lists/*

# --- Node.js 20 LTS ---
# Installed directly from NodeSource rather than the devcontainer feature so the
# image is fully self-contained and devshell-docker.sh has feature parity.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# --- .NET 9 ---
# Microsoft's dotnet-install.sh is the cross-distro canonical install method.
RUN curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && chmod +x /tmp/dotnet-install.sh \
    && /tmp/dotnet-install.sh --channel 9.0 --install-dir /usr/local/dotnet \
    && rm /tmp/dotnet-install.sh

ENV DOTNET_ROOT=/usr/local/dotnet
ENV PATH="$PATH:/usr/local/dotnet"

# --- xmake ---
# The install script emits a non-fatal error when sourcing ~/.xmake/profile
# because xmake refuses to run as root without --root. We suppress that exit
# code, then verify the install explicitly with --root.
# XMAKE_ROOT=y makes every subsequent xmake invocation root-safe without
# needing the flag on every call.
ENV XMAKE_ROOT=y
RUN curl -fsSL https://xmake.io/shget.text | bash 

ENV XMAKE_BUILD_PATH=/root/.local/bin
RUN $XMAKE_BUILD_PATH/xmake --root --version

# --- xwin (pre-built musl binary — no Rust toolchain needed) ---
ARG XWIN_VERSION=0.6.5
RUN curl -fsSL \
        "https://github.com/Jake-Shadle/xwin/releases/download/${XWIN_VERSION}/xwin-${XWIN_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
    | tar -xz --strip-components=1 \
        -C /usr/local/bin \
        "xwin-${XWIN_VERSION}-x86_64-unknown-linux-musl/xwin" \
    && chmod +x /usr/local/bin/xwin

# --- Windows SDK + MSVC CRT headers/libs via xwin ---
# Targets x86_64 only (SKSE64 / CommonLibSSE-NG). ~700MB download; cached in
# this layer so rebuilds don't re-fetch.
# Microsoft EULA accepted here — these files are for build-time use only.
ENV XWIN_ACCEPT_LICENSE=true
RUN xwin splat --output /opt/xwin
