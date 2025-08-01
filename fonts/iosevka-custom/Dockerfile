# syntax=docker/dockerfile:1.4

# -----------------------------------------------------------------------------
#     Build Iosevka font with custom settings.
# -----------------------------------------------------------------------------
FROM node:20-bullseye-slim AS builder

# Version from https://github.com/be5invis/Iosevka/releases/.
ARG FONT_VERSION=30.3.2
ARG FONT_SHA256SUM=0add730597a747893274f1719b59002ea779fa4ce6a87bf313b1a9c2efb88bd8

WORKDIR /iosevka

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ttfautohint \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL --proto '=https' --tlsv1.2 \
    https://github.com/be5invis/Iosevka/archive/v${FONT_VERSION}.tar.gz \
    -o iosevka.tar.gz \
    && echo "${FONT_SHA256SUM} iosevka.tar.gz" | sha256sum -c - \
    && tar xzf iosevka.tar.gz --strip-components=1 \
    && rm iosevka.tar.gz

COPY --link private-build-plans.toml .

RUN npm ci \
    && npm run build -- ttf::iosevka-custom
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#     Patch Iosevka font with Nerd Fonts glyphs.
# -----------------------------------------------------------------------------
FROM node:20-bullseye-slim AS patcher

ARG NERD_FONTS_VERSION=v3.2.1

RUN apt-get update && apt-get install -y --no-install-recommends \
    fontforge \
    python3-fontforge \
    python3-pip \
    git \
    parallel \
    fd-find \
    && rm -rf /var/lib/apt/lists/*

# Download Nerd Fonts patcher and glyphs
RUN git clone --depth 1 --filter=blob:none  --no-checkout --branch ${NERD_FONTS_VERSION} https://github.com/ryanoasis/nerd-fonts /nerd-fonts \
    && cd /nerd-fonts \
    && git sparse-checkout set font-patcher src/glyphs src/svgs bin \
    && git checkout

# Patch Iosevka fonts with Nerd Fonts glyphs
RUN tee /patch-font.sh <<EOF
#!/usr/bin/env bash

set -euo pipefail

echo "Patching font: \$1"
ls -l "\$1"

fontforge -script /nerd-fonts/font-patcher \
    --mono \
    --adjust-line-height \
    --complete \
    --careful \
    --no-progressbars \
    --outputdir /patched-fonts \
    "\$1"
EOF
RUN chmod +x /patch-font.sh

COPY --from=builder /iosevka/dist/iosevka-custom/TTF/ /fonts-to-patch/
RUN ls -l /fonts-to-patch

RUN mkdir -p /patched-fonts \
    && fdfind --type file --extension ttf . /fonts-to-patch/ \
    | parallel /patch-font.sh
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#     Export patched fonts.
# -----------------------------------------------------------------------------
FROM scratch AS output
COPY --from=patcher /patched-fonts /dist
