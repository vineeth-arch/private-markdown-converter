-- Private Markdown Converter Launcher
-- Calls the bundled helper script, which delegates to launch.sh

on run
    set launchScript to POSIX path of (path to resource "launch-helper.sh" in directory "scripts")
    do shell script "bash " & quoted form of launchScript & " > /dev/null 2>&1 &"
end run
