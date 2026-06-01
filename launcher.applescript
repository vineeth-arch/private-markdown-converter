-- Private Markdown Converter Launcher
-- Starts the local service on run/reopen and stops it on quit

on run
    my launchApp()
    return 30
end run

on reopen
    my launchApp()
end reopen

on idle
    return 30
end idle

on quit
    my stopApp()
    continue quit
end quit

on launchApp()
    set launchScript to POSIX path of (path to resource "launch-helper.sh" in directory "scripts")
    do shell script "bash " & quoted form of launchScript & " > /dev/null 2>&1 &"
end launchApp

on stopApp()
    set stopScript to POSIX path of (path to resource "stop-helper.sh" in directory "scripts")
    do shell script "bash " & quoted form of stopScript & " > /dev/null 2>&1"
end stopApp
