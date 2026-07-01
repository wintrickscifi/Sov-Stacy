<?php
setlocale(LC_CTYPE, 'en_US.UTF-8');

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json");

// ------------------------------------------------------------
// 1. AUDIO MODE (multipart/form-data)
// ------------------------------------------------------------
if (!empty($_FILES['audio'])) {

    // Save uploaded audio
    $audioPath = "voice.webm";
    move_uploaded_file($_FILES['audio']['tmp_name'], $audioPath);

    // Whisper.cpp paths
    $whisperBin = "/home/ronaldwi/whisper.cpp/main";
    $modelPath  = "/home/ronaldwi/whisper.cpp/models/base.en.bin";

    // Run Whisper.cpp transcription
    $cmd = escapeshellcmd("$whisperBin -m $modelPath -f $audioPath -otxt");
    shell_exec($cmd);

    // Whisper.cpp outputs: voice.webm.txt
    $transcriptFile = $audioPath . ".txt";
    $transcript = file_exists($transcriptFile)
        ? trim(file_get_contents($transcriptFile))
        : "";

    // If no transcript, return error
    if ($transcript === "") {
        echo json_encode([
            "transcript" => "",
            "response" => "Clause of Silence: No voice was captured."
        ]);
        exit;
    }

    // --------------------------------------------------------
    // Feed transcript into your existing Python pipeline
    // --------------------------------------------------------
    $arg1 = escapeshellarg($transcript);
    $arg2 = escapeshellarg("Clause of Voice");
    $arg3 = escapeshellarg("");

    $command = "python main.py $arg1 $arg2 $arg3 2>&1";
    $output = shell_exec($command);

    echo json_encode([
        "transcript" => $transcript,
        "response" => trim($output)
    ]);
    exit;
}

// ------------------------------------------------------------
// 2. TEXT MODE (your original JSON logic)
// ------------------------------------------------------------
$raw_input = file_get_contents('php://input');
$data = json_decode($raw_input, true);

$history = isset($data['history']) ? $data['history'] : [];
$clause  = isset($data['clause']) ? $data['clause'] : 'Clause of State';

$last_message = "";

// Match keys
if (isset($data['message']) && trim($data['message']) !== '') {
    $last_message = trim($data['message']);
}
elseif (isset($data['user']) && trim($data['user']) !== '') {
    $last_message = trim($data['user']);
}
elseif (isset($data['input']) && trim($data['input']) !== '') {
    $last_message = trim($data['input']);
}
elseif (!empty($history)) {
    $last_item = end($history);
    if ($last_item['role'] === 'user') {
        $last_message = $last_item['content'];
    }
}

// Format last 6 exchanges
$history_without_current = array_slice($history, 0, -1);
$recent_history = array_slice($history_without_current, -6);

$formatted_history = "";
foreach ($recent_history as $msg) {
    $role = ($msg['role'] === 'user') ? 'User' : 'sov_stacy';
    $formatted_history .= "[{$role}]: " . $msg['content'] . "\n";
}

// Escape args for Python
$arg1 = escapeshellarg($last_message);
$arg2 = escapeshellarg($clause);
$arg3 = escapeshellarg(trim($formatted_history));

// Execute Python
$command = "python main.py {$arg1} {$arg2} {$arg3} 2>&1";
$output = shell_exec($command);

// Debug log
file_put_contents('gateway_debug.txt',
    "--- NEW REQUEST ---\nRAW INPUT: " . $raw_input .
    "\nEXTRACTED USER MESSAGE: " . $last_message .
    "\nEXECUTED COMMAND: " . $command .
    "\n-------------------\n\n",
    FILE_APPEND
);

// Return JSON
echo json_encode([
    "response" => trim($output)
]);
?>
