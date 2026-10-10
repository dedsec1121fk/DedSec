#!/usr/bin/env bash
# Shared first-install legal gate; must be sourced by setup entry points.
# No package operations or profile modifications occur before the user accepts.
DEDSEC_LEGAL_DIR="${ROOT_DIR}/Important Documents"
DEDSEC_LEGAL_EN="${DEDSEC_LEGAL_DIR}/Legal Disclaimer English Version.txt"
DEDSEC_LEGAL_GR="${DEDSEC_LEGAL_DIR}/Legal Disclaimer Greek Version.txt"
DEDSEC_LEGAL_EN_ORIGINAL="${DEDSEC_LEGAL_DIR}/Legal Disclaimer English Version.docx"
DEDSEC_LEGAL_GR_ORIGINAL="${DEDSEC_LEGAL_DIR}/Legal Disclaimer Greek Version.docx"
DEDSEC_LEGAL_STATE="${HOME:-$ROOT_DIR}/.local/state/dedsec/legal-acceptance-v1.txt"

_dedsec_legal_digest() {
  if command -v sha256sum >/dev/null 2>&1; then
    # Digest the originals: acceptance must be renewed when legal wording changes.
    sha256sum "$DEDSEC_LEGAL_EN_ORIGINAL" "$DEDSEC_LEGAL_GR_ORIGINAL" | cut -d' ' -f1 | sha256sum | cut -d' ' -f1
  else
    # POSIX cksum is a fallback for minimal Termux installations.
    cksum "$DEDSEC_LEGAL_EN_ORIGINAL" "$DEDSEC_LEGAL_GR_ORIGINAL" | awk '{print $1":"$2}' | cksum | awk '{print $1":"$2}'
  fi
}

_dedsec_legal_show() {
  local file="$1"
  if [ ! -r "$file" ]; then
    printf '[error] Cannot read legal document: %s\n' "$file" >&2
    return 1
  fi
  printf '\n===== %s =====\n' "$(basename "$file")"
  if [ -t 1 ] && command -v less >/dev/null 2>&1; then
    less -R "$file"
  elif [ -t 1 ] && command -v more >/dev/null 2>&1; then
    more "$file"
  else
    cat "$file"
  fi
  printf '\n===== End of document =====\n'
}

dedsec_require_legal_acceptance() {
  local digest answer
  for file in "$DEDSEC_LEGAL_EN" "$DEDSEC_LEGAL_GR" "$DEDSEC_LEGAL_EN_ORIGINAL" "$DEDSEC_LEGAL_GR_ORIGINAL"; do
    [ -r "$file" ] || { printf '[error] Required legal file missing: %s\n' "$file" >&2; return 1; }
  done
  digest="$(_dedsec_legal_digest)" || return 1
  if [ -r "$DEDSEC_LEGAL_STATE" ] && [ "$(cat "$DEDSEC_LEGAL_STATE")" = "$digest" ]; then
    printf '[legal] Previously accepted legal documents are unchanged.\n'
    return 0
  fi

  printf '\n===========================================================\n'
  printf ' DEDSEC PROJECT - LEGAL TERMS / ΝΟΜΙΚΟΙ ΟΡΟΙ\n'
  printf '===========================================================\n'
  printf 'You must accept the legal documents BEFORE installation.\n'
  printf 'Πρέπει να αποδεχθείτε τους νομικούς όρους ΠΡΙΝ την εγκατάσταση.\n'
  printf 'Official originals are in: Important Documents/ (*.docx)\n'
  printf ' [y / Enter] Accept / Αποδοχή\n'
  printf ' [n]         Decline / Άρνηση (setup stops; you may retry later)\n'
  printf ' [r]         Reading choices / Επιλογές ανάγνωσης\n'
  printf ' [re]        Read complete English document\n'
  printf ' [rg]        Ανάγνωση πλήρους ελληνικού εγγράφου\n\n'

  while :; do
    printf 'Legal choice [y/Enter/n/r/re/rg]: '
    if ! IFS= read -r answer; then
      printf '\n[legal] Input unavailable. Setup cancelled without accepting.\n' >&2
      return 1
    fi
    answer="${answer,,}"
    case "$answer" in
      ''|y|yes)
        # Only persist acceptance after explicit input (Enter means accept as requested).
        mkdir -p "$(dirname "$DEDSEC_LEGAL_STATE")" || return 1
        (umask 077 && printf '%s\n' "$digest" > "$DEDSEC_LEGAL_STATE") || return 1
        printf '[legal] Accepted. Starting DedSec setup.\n'
        return 0
        ;;
      n|no)
        printf '[legal] Declined. No setup changes made. Re-run Setup.sh to try again.\n'
        return 1
        ;;
      r)
        printf 'Choose re (English) or rg (Ελληνικά). Both documents remain available.\n'
        ;;
      re) _dedsec_legal_show "$DEDSEC_LEGAL_EN" || return 1 ;;
      rg) _dedsec_legal_show "$DEDSEC_LEGAL_GR" || return 1 ;;
      *) printf '[legal] Invalid choice. Use y, Enter, n, r, re, or rg.\n' ;;
    esac
  done
}
