__autocol="$(cd "${0%/*}"; pwd)/autocol.py"
type python3 >/dev/null 2>&1 && alias autocol="python3 $__autocol" || alias domr="$__autocol"
unset __autocol
