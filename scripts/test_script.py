# Open a capture file handle
cap = rd.OpenCaptureFile()

# Open a particular file - see also OpenBuffer to load from memory
fullPath = "F:\\thesis\\renderdoc_files\\captures\\renderdoc_files-frame17461.rdc"
status = cap.OpenFile(fullPath, '', None)

# Make sure the file opened successfully
if status != rd.ReplayStatus.Succeeded:
    raise RuntimeError("Couldn't open file: " + str(status))

# Make sure we can replay
if not cap.LocalReplaySupport():
    raise RuntimeError("Capture cannot be replayed")

# Initialise the replay
status,controller = cap.OpenCapture(None)

if status != rd.ReplayStatus.Succeeded:
    raise RuntimeError("Couldn't initialise replay: " + str(status))


controller