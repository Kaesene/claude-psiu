# Windows implementation. Reads from environment (set by notify.sh):
#   PHRASE, TOAST_TITLE, TOAST_BODY, SOUND, NOTIFY_EVENT
#   NOTIFY_ENABLE_SOUND, NOTIFY_ENABLE_TOAST, NOTIFY_ENABLE_TTS
#   NOTIFY_VOICE, NOTIFY_RATE, NOTIFY_VOLUME

$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$phrase     = $env:PHRASE
$toastTitle = if ($env:TOAST_TITLE) { $env:TOAST_TITLE } else { 'Claude Code' }
$toastBody  = if ($env:TOAST_BODY)  { $env:TOAST_BODY }  else { '' }
$soundName  = $env:SOUND
$eventName  = if ($env:NOTIFY_EVENT) { $env:NOTIFY_EVENT } else { 'stop' }

$enableSound = ($env:NOTIFY_ENABLE_SOUND -ne '0')
$enableToast = ($env:NOTIFY_ENABLE_TOAST -ne '0')
$enableTts   = ($env:NOTIFY_ENABLE_TTS   -ne '0')

# ---- Sound -----------------------------------------------------------------
if ($enableSound) {
    if (-not $soundName) {
        $soundName = switch ($eventName) {
            'stop_failure' { 'Hand' }
            'notification' { 'Exclamation' }
            default        { 'Asterisk' }
        }
    }
    # Allow either a system sound name (Asterisk/Beep/Exclamation/Hand/Question)
    # or a full path to a .wav file.
    if (Test-Path -LiteralPath $soundName -PathType Leaf) {
        try {
            $player = New-Object System.Media.SoundPlayer $soundName
            $player.Play()
        } catch {}
    } else {
        try {
            switch ($soundName) {
                'Asterisk'    { [System.Media.SystemSounds]::Asterisk.Play() }
                'Beep'        { [System.Media.SystemSounds]::Beep.Play() }
                'Exclamation' { [System.Media.SystemSounds]::Exclamation.Play() }
                'Hand'        { [System.Media.SystemSounds]::Hand.Play() }
                'Question'    { [System.Media.SystemSounds]::Question.Play() }
                default       { [System.Media.SystemSounds]::Asterisk.Play() }
            }
        } catch {}
    }
}

# ---- Toast -----------------------------------------------------------------
if ($enableToast -and $toastBody) {
    $toastDone = $false
    try {
        Import-Module BurntToast -ErrorAction Stop
        New-BurntToastNotification -Text $toastTitle, $toastBody
        $toastDone = $true
    } catch {}

    if (-not $toastDone) {
        # Fallback: WinRT ToastNotificationManager (no module required, Win10+)
        try {
            [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]
            [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime]
            $title = [System.Security.SecurityElement]::Escape($toastTitle)
            $body  = [System.Security.SecurityElement]::Escape($toastBody)
            $xml = @"
<toast><visual><binding template="ToastGeneric"><text>$title</text><text>$body</text></binding></visual></toast>
"@
            $doc = New-Object Windows.Data.Xml.Dom.XmlDocument
            $doc.LoadXml($xml)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $doc
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show($toast)
        } catch {}
    }
}

# ---- TTS -------------------------------------------------------------------
if ($enableTts -and $phrase) {
    try {
        Add-Type -AssemblyName System.Speech
        $s = New-Object System.Speech.Synthesis.SpeechSynthesizer

        if ($env:NOTIFY_VOICE) {
            try { $s.SelectVoice($env:NOTIFY_VOICE) } catch {}
        }
        if ($env:NOTIFY_RATE) {
            try { $s.Rate = [int]$env:NOTIFY_RATE } catch {}
        }
        if ($env:NOTIFY_VOLUME) {
            try { $s.Volume = [int]$env:NOTIFY_VOLUME } catch {}
        }
        $s.Speak($phrase) | Out-Null
        $s.Dispose()
    } catch {}
}
