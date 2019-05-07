# RenderDoc Python console, powered by python 3.6.4.
# The 'pyrenderdoc' object is the current CaptureContext instance.
# The 'renderdoc' and 'qrenderdoc' modules are available.
# Documentation is available: https://renderdoc.org/docs/python_api/index.html

rd = renderdoc 

# frameInfo = renderdoc.ReplayController.GetFrameInfo()
fileName = "G:\\thesis_data\\renderdoc_files\\renderdoc_files-frame6481.rdc"
# Open a capture file handle
cap = rd.OpenCaptureFile()

# Open a particular file - see also OpenBuffer to load from memory
status = cap.OpenFile(fileName, '', None)

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

# Now we can use the controller!
print("%d top-level drawcalls" % len(controller.GetDrawcalls()))

frameInfo = controller.GetFrameInfo()
frameId = frameInfo.frameNumber
print(frameId)


# TODO add reference to playing-for-data

config = {}
config['save_dir'] = 'G:\\thesis_data\\renderdoc_files\\processed' # where we store extraction results
config['gbufferpass_colortargets'] = 4 # number of color targets that identify the G-buffer pass, most probably 4 as games want to use all available render targets
config['gbufferpass_hasdepth']     = True # whether G-buffer pass has a depth target
# Our names for the color buffers
config['gbuffer_names']            = ['gbuffer1', 'gbuffer2', 'gbuffer3', 'gbuffer4'] # the number should match the config['gbufferpass_colortargets']

# Get drawcalls
drawcalls = controller.GetDrawcalls()
print('Found %d drawcalls.' % len(drawcalls))

def containsTargets(drawcallName, numColorTargets, hasDepthTarget):
	""" Determines if drawcall has multiple render targets by checking its name. 
	    The name is defined by renderdoc and contains information about render targets."""	
	print("drawcall Name is: {}".format(drawcallName))
	if hasDepthTarget:
		return drawcallName.find('(%d Targets + Depth)' % numColorTargets) >= 0		
	else:		
		return drawcallName.find('(%d Targets)' % numColorTargets) >= 0		
	pass

def findGbufferPass(numColorTargets, hasDepthTarget):
	""" Identifies the G-buffer pass. """
	gbufferEnd = 0
	gbufferIds = [i for i,call in enumerate(drawcalls) if containsTargets(call.name, numColorTargets, hasDepthTarget)]
	print("there are %d gbuffer IDs" %len(gbufferIds))
	if len(gbufferIds) == 1:
		gbufferId    = gbufferIds[0]
		gbufferCalls = drawcalls[gbufferId].children
		print('G-buffer pass has %d drawcalls.' % len(gbufferCalls))
		gbufferEnd   = drawcalls[gbufferId].children[-1].eventID # last drawcall of the G-buffer pass
	
	assert(gbufferEnd > 0, 'Did not find any drawcall with the specified G-buffer settings.')
	return gbufferId, gbufferEnd
	
def findFinalPass(numColorTargets, hasDepthTarget, drawCallName):
	""" Returns the EventID of the pass that draws the final image (before HUD). """

	# Find last drawcall before HUD
	potentialHudIds = [i for i,call in enumerate(drawcalls) if containsTargets(call.name, numColorTargets, hasDepthTarget)]
	print('Found %d potential HUD passes.' % len(potentialHudIds))

	colorpassIds = [i for i,call in enumerate(drawcalls) if containsTargets(call.name, 1, False)]

	a = colorpassIds[:]
	a.extend(potentialHudIds[:-3])
	assert(len(a) > 0, 'Found not enough potential final passes.')
	firstPotentialFinalId = max(a)

	finalPassId = 0
	return [call.eventID for call in drawcalls[-1:0:-1] if call.name.find(drawCallName) >= 0][1]
	
def getColorBuffers(frameId, eventId):
	""" Sets the pipeline to eventId and returns the ids of bound render targets. """
	renderdoc.SetEventID(None, frameId, eventId)
	commonState   = renderdoc.CurPipelineState
	outputTargets = commonState.GetOutputTargets()
	return [t for t in outputTargets if str(t) != '0']

gbufferId, gbufferEnd = findGbufferPass(config['gbufferpass_colortargets'], config['gbufferpass_hasdepth'])
print('G-buffer pass is done at EID %d.' % gbufferEnd)
bufferIds = getColorBuffers(frameId, gbufferEnd)

# Save color targets
for i,bid in enumerate(bufferIds):
 	renderdoc.SaveTexture(bid, '{0}/{1}_{2}.png'.format(saveDir, "test", config['gbuffer_names'][i]))


# Shutdown the controller first, then the capture file
controller.Shutdown()

cap.Shutdown()