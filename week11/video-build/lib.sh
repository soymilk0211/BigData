# shared helpers for terminal scenes (anonymized: no user/host/path in prompt)
export LANG=C.UTF-8 PS1='$ ' COLUMNS=110
cd /tmp/demo/skill
clear
banner(){ printf '\e[1;30;43m  %s  \e[0m\n\n' "$1"; }
note(){ printf '\e[1;36m# %s\e[0m\n' "$1"; sleep ${2:-1.2}; }
type_cmd(){ printf '\e[1;32m$\e[0m '; local s="$1" i; for ((i=0;i<${#s};i++)); do printf '%s' "${s:i:1}"; sleep 0.018; done; echo; }
mask(){ sed -u -E -e "s#/tmp/demo/skill/##g" -e "s#/tmp/[^ \"']*#<TMP>#g" -e "s#/home/[^/ \"]+#~#g" -e "s#/workspace[^ \"]*#<WS>#g"; }
run(){ type_cmd "$1"; sleep 0.4; eval "$1" 2>&1 | mask; sleep ${2:-1.5}; }
