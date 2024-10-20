__autocol="$(cd "${BASH_SOURCE%/*}"; pwd)/autocol.py"
type python3 >/dev/null 2>&1 && alias autocol="python3 $__autocol" || alias autocol="$__autocol"
unset __autocol
