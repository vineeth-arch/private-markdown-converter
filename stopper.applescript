on run
    set stopScript to POSIX path of (path to resource "stop-helper.sh" in directory "scripts")
    do shell script "bash " & quoted form of stopScript & " > /dev/null 2>&1"
    display notification "Private Markdown Converter stopped." with title "Private Markdown Converter"
end run
