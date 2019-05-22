# this script includes some code snippets from https://renderdoc.org/docs/python_api/examples/renderdoc/ by Baldur Karlsson from 2019
# and playing-for-data https://bitbucket.org/visinf/projects-2016-playing-for-data/src/master/scripts/extract_from_game.py by Richter et al 2016


import renderdoc as rd
import os


config = {}
config['file_dir'] = 'F:\\thesis\\renderdoc_files\\captures' # where .rdc capture files are stored
config['save_dir'] = 'F:\\thesis\\renderdoc_files\\processed' # where we store extraction results

# find depth pass
def getDepthPass(drawcalls):    
    foundDepthPass = False
    searchFromId = 1000 # adjust to the eventId around which the DepthPass starts
    for d in drawcalls:
        if (d.eventId > searchFromId) and (d.name.find("Dispatch") >= 0):
            foundDepthPass = True
        
        if foundDepthPass:
            print('found depthPass with eventId: {}'.format(d.previous.eventId))
            return d.previous

# find final drawcall before HUD is rendereddef getFinalPass(drawcalls):
    foundFinalPass = False
    for d in drawcalls[::-1]:
        if foundFinalPass:            return d

        if d.name.find("ClearRenderTargetView") >= 0:
            foundFinalPass = True

def saveDepth(controller, drawcalls, file_prefix):
    depthsave = rd.TextureSave()
    print('saving depth')
    filePath = '{0}\\{1}_depth.exr'.format(config['save_dir'], file_prefix)
    fileName = filePath.split('\\')[-1]
    if fileName not in os.listdir(config['save_dir']):
        depthsave.destType = rd.FileType.EXR
        
        depthsave.channelExtract = 0
        depthPass = getDepthPass(drawcalls)
        depthPassId = depthPass.eventId
        
        controller.SetFrameEvent(depthPassId, True)
        depthsave.resourceId = depthPass.depthOut
        print("resourceId of depth texture is {}".format(depthsave.resourceId))
        
        # adjust white and black to min and max pixel values
        depthOutput = controller.CreateOutput(rd.CreateHeadlessWindowingData(), rd.ReplayOutputType.Headless)
        textureDisplay = rd.TextureDisplay()
        textureDisplay.resourceId = depthPass.depthOut
        depthOutput.SetTextureDisplay(textureDisplay)
        min, max = depthOutput.GetMinMax()
        
        controller.SaveTexture(depthsave, filePath)
        print('depth saved')    else:
        print('depth-map of {} already exists and is therefore skipped'.format(file_prefix))

def saveRGB(controller, drawcalls, file_prefix):
    RGBsave = rd.TextureSave()
    filePath = '{0}\\{1}_final.png'.format(config['save_dir'], file_prefix)
    fileName = filePath.split('\\')[-1]
    if fileName not in os.listdir(config['save_dir']):
        print('filename {} is not yet in this directory'.format(fileName))
        RGBsave.destType = rd.FileType.PNG
    
        finalPass = getFinalPass(drawcalls)
        finalPassId = finalPass.eventId
    
        controller.SetFrameEvent(finalPassId, True)
        RGBsave.resourceId = finalPass.outputs[0]
        controller.SaveTexture(RGBsave, filePath)
    else:
        print('RGB image of {} already exists and is therefore skipped'.format(file_prefix))

def saveCamParams(controller, drawcalls, file_prefix):
    pass

def process(fileName):
    # Open a capture file handle
    cap = rd.OpenCaptureFile()

    # Open a particular file - see also OpenBuffer to load from memory
    fullPath = config['file_dir'] + '\\' + fileName
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

    # Get drawcalls
    drawcalls = controller.GetDrawcalls()
    
    file_prefix = fileName[:-4] # remove .rdc ending
    saveRGB(controller, drawcalls, file_prefix)
    saveDepth(controller, drawcalls, file_prefix)
    # saveCamParams(controller, drawcalls, file_prefix) #TODO implement this function
    
    # Shutdown the controller first, then the capture file
    controller.Shutdown()

    cap.Shutdown()

def main():
    for f in os.listdir(config['file_dir']):
        print("processing {}".format(f))
        process(f)
        break

    print('finished processing all files in {}'.format(config['file_dir']))
    print('processed files were saved to {}'.format(config['save_dir']))

main()
