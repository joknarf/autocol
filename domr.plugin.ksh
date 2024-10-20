# must cd to location of this file before sourcing as ksh cannot determine sourced file location
__autocol="$PWD/autocol.py"
type python3 >/dev/null 2>&1 && alias autocol="python3 $__autocol" || alias domr="$__autocol"
unset __autocol
