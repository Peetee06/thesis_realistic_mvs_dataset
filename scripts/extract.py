# this script includes some code snippets from https://renderdoc.org/docs/python_api/examples/renderdoc/ by Baldur Karlsson from 2019
# and playing-for-data https://bitbucket.org/visinf/projects-2016-playing-for-data/src/master/scripts/extract_from_game.py by Richter et al 2016


import renderdoc as rd
import os


config = {}
config['file_dir'] = 'G:\\thesis_data\\renderdoc_files\\captures' # where .rdc capture files are stored
config['save_dir'] = 'G:\\thesis_data\\renderdoc_files\\processed' # where we store extraction results

# set up saving textures
texsave = rd.TextureSave()

# find depth pass
def getDepthPass(drawcalls):
    pass

# find final drawcall before HUD is rendereddef getFinalPass(drawcalls):
    foundFinalPass = False
    for d in drawcalls[::-1]:
        if foundFinalPass:            return d

        if d.name.find("ClearRenderTargetView") >= 0:
            foundFinalPass = True

def saveDepth(controller, drawcalls, file_prefix):
    filePath = '{0}\\{1}_depth.exr'.format(config['save_dir'], file_prefix)
    fileName = filePath.split('\\')[-1]
    if fileName not in os.listdir(config['save_dir']):
        texsave.destType = rd.FileType.EXR
        
        depthPass = getDepthPass(drawcalls)
        depthPassId = depthPass.eventId
        
        controller.SetFrameEvent(depthDraw, True)
        texsave.resourceId = depthPass.depthOut
        controller.SaveTexture(texsave, )    else:
        print('depth-map of {} already exists and is therefore skipped'.format(file_prefix))

def saveRGB(controller, drawcalls, file_prefix):
    filePath = '{0}\\{1}_final.png'.format(config['save_dir'], file_prefix)
    fileName = filePath.split('\\')[-1]
    if fileName not in os.listdir(config['save_dir']):
        print('filename {} is not yet in this directory'.format(fileName))
        texsave.destType = rd.FileType.PNG
    
        finalPass = getFinalPass(drawcalls)
        finalPassId = finalPass.eventId
    
        controller.SetFrameEvent(finalPassId, True)
        texsave.resourceId = finalPass.outputs[0]
        controller.SaveTexture(texsave, fileName)
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
    # saveDepth(controller, drawcalls, file_prefix)
    # saveCamParams(controller, drawcalls, file_prefix) #TODO implement this function
    
    # Shutdown the controller first, then the capture file
    controller.Shutdown()

    cap.Shutdown()

def main():
    for f in os.listdir(config['file_dir']):
        print(f)
        process(f)

    print('finished processing all files in {}'.format(config['file_dir']))
    print('processed files were saved to {}'.format(config['save_dir']))

main()
