lastPath = "C:\\Program Files\\Microsoft Games\\Halo Custom Edition\\data\\"
saveDir = undefined

frameCount = 0
nodeListChecksum = 0
nodeNames = #()
nodeArray = #()
nodeArraySorted = #()
nodeChildIndices = #()
nodeFirstChildIndices = #()
nodeNextSiblingIndices = #()
rootSceneNode = undefined

rollout animExporter "Animation Exporter" width:400 height:343
(
	activeXControl animExportQueue "MSComctlLib.ListViewCtrl.2" pos:[7,7] width:386 height:155
	dropDownList animType "" pos:[7,168] width:193 height:21 items:#("JMA (base; dx,dy)", "JMO (overlay; none)", "JMR (replacement; none)", "JMM (base; none)", "JMT (base; dx,dy,dyaw)", "JMZ (base; dx,dy,dz,dyaw)", "JMW (base; none; world-relative)") selection:1
	button animRemoveUnchecked "- Unchecked" pos:[318,168] width:75 height:20
	button animAddFile "+ File" pos:[206,168] width:50 height:20
	button animAddFolder "+ Folder" pos:[262,168] width:50 height:20

	groupBox groupSave "Save Parameters" pos:[7,191] width:386 height:77
	radioButtons saveMethod "" pos:[16,206] width:220 height:32 labels:#("Save Exported Files to Original Directories", "Save Exported Files to...") columns:1
	button saveDirPick "Pick" pos:[15,241] width:35 height:19 enabled:false
	button saveDirClear "Clear" pos:[54,241] width:35 height:19 enabled:false
	editText saveDirText "" pos:[89,241] width:296 height:19 enabled:false

	groupBox groupExecute "Execute" pos:[7,270] width:386 height:53
	button exportAnim "Export Animation" pos:[125,287] width:150 height:25
	
	label credits "Zteam - CtrlAltDestroy" pos:[8,326] width:103 height:13 enabled:false
	
	fn calcNodeListChecksum =
	(
		nodeListCheck = 0
		for i = 1 to nodeArraySorted.count do
		(
			nodeCheck = 0
			for j = 1 to nodeArraySorted[i].name.count do (nodeCheck += bit.charAsInt nodeArraySorted[i].name[j])
			nodeCheck *= (nodeArraySorted.count * (nodeFirstChildIndices[i] + nodeNextSiblingIndices[i]))
			nodeListCheck += nodeCheck
		)
		return nodeListCheck
	)
	
	fn flushInstances =
	(
		frameCount = 0
		nodeListChecksum = 0
		nodeNames = #()
		nodeArray = #()
		nodeArraySorted = #()
		nodeChildIndices = #()
		nodeFirstChildIndices = #()
		nodeNextSiblingIndices = #()
		rootSceneNode = undefined
	)
	
	fn indexNodes =
	(
		failed = false
		
		try
		(
			nodeArray = (($'frame*' as array) + ($'bip01*' as array))
			nodeArray = for i in nodeArray where (not i.isHidden) collect i
			for w = 1 to nodeArray.count do
			(
				if (nodeArray[w].parent != undefined) then
				(
					if (((substring nodeArray[w].parent.name 1 5 as name) != ("frame" as name)) and ((substring nodeArray[w].parent.name 1 5 as name) != ("bip01" as name))) then
					(
						failed = true
						exit
					)
				)
			)
			if not failed then
			(
				for i = 1 to nodeArray.count do
				(
					if (nodeArray[i].parent == undefined) then
					(
						if (rootSceneNode != undefined) then
						(
							failed = true
							exit
						)
						else
						(
							rootSceneNode = nodeArray[i]
							nodeArray[i].name = ("01" + nodeArray[i].name)
						)
					)
					else
					(
						tempParentNode = nodeArray[i].parent
						n = 1
						do
						(
							tempRootSceneNode = tempParentNode
							tempParentNode = tempParentNode.parent
							n += 1
						)
						while (tempParentNode != undefined)
						
						if (tempRootSceneNode != rootSceneNode) then
						(
							failed = true
							exit
						)
						else
						(
							if n < 10 then (nodeArray[i].name = ("0" + (n as string) + nodeArray[i].name))
							else (nodeArray[i].name = ((n as string) + nodeArray[i].name))
						)
					)
				)
				if not failed then
				(
					nodeNames = for j in nodeArray collect j.name
					sort nodeNames
					for k = 1 to nodeArray.count do (nodeArraySorted[k] = getNodeByName nodeNames[k])
					for h = 1 to nodeArray.count do (nodeArray[h].name = (substring nodeArray[h].name 3 -1))
					nodeNames = for j in nodeArray collect j.name
					
					for b = 1 to nodeArraySorted.count do
					(
						tempNodeChildIndices = #()
						for c = 1 to nodeArraySorted[b].children.count do
						(
							tempNodeChild = nodeArraySorted[b].children[c]
							if (tempNodeChild != undefined) then
							(
								tempChildIndex = findItem nodeArraySorted tempNodeChild
								if	(tempChildIndex != 0) then (append tempNodeChildIndices tempChildIndex)
							)
						)
						nodeChildIndices[b] = tempNodeChildIndices
						if (nodeChildIndices[b].count == 0) then (nodeFirstChildIndices[b] = 0)
						else
						(
							sort nodeChildIndices[b]
							nodeFirstChildIndices[b] = nodeChildIndices[b][1]
						)
					)
					
					nodeNextSiblingIndices[1] = 0
					for s = 1 to nodeChildIndices.count do
					(
						if ((nodeChildIndices[s].count < 2) and (nodeChildIndices[s][1] != undefined)) then (nodeNextSiblingIndices[nodeChildIndices[s][1]] = 0)
						else
						(
							for f = 1 to nodeChildIndices[s].count do
							(
								if (f == nodeChildIndices[s].count) then (nodeNextSiblingIndices[nodeChildIndices[s][f]] = 0)
								else (nodeNextSiblingIndices[nodeChildIndices[s][f]] = nodeChildIndices[s][f + 1])
							)
						)
					)
				)
			)
			if failed then
			(
				for i in nodeArray do
				(
					if (((substring i.name 1 5 as name) != ("frame" as name)) and ((substring i.name 1 5 as name) != ("bip01" as name))) then (i.name = (substring i.name 3 -1))
					nodeNames = #()
					nodeArraySorted = #()
				)
			)
			
		)
		catch
		(
			failed = true
		)
		
		return failed
	)
	
	fn writeAnim target =
	(
		frameCount = ((animationRange.end as integer)/160) + 1
		nodeListChecksum = calcNodeListChecksum()
		
		format "%\n" 16392 to:target
		format "%\n" frameCount to:target
		format "%\n" frameRate to:target
		format "%\n" 1 to:target
		format "%\n" "unnamedActor" to:target
		format "%\n" nodeArraySorted.count to:target
		format "%\n" nodeListChecksum to:target
		
		for i = 1 to nodeArraySorted.count do
		(
			format "%\n" nodeArraySorted[i].name to:target
			format "%\n" (nodeFirstChildIndices[i] - 1) to:target
			format "%\n" (nodeNextSiblingIndices[i] - 1) to:target
		)
		
		tempNodes = #()
		for a = 1 to nodeArraySorted.count do
		(
			tempNode = Box length:0.5 width:0.5 height:0.5
			tempNode.name = ("temp__" + nodeArraySorted[a].name)
			tempNode.wirecolor = color 255 0 0
			tempNodes[a] = tempNode
		)
		for b = 1 to tempNodes.count do
		(
			try (tempNodes[b].parent = tempNodes[(findItem nodeArraySorted nodeArraySorted[b].parent)])
			catch ()
		)
		
		max tool animmode
		set animate on
		
		sliderTime = 0
		for j = 1 to frameCount do
		(
			for d = 1 to tempNodes.count do (tempNodes[d].transform = nodeArraySorted[d].transform)
			for k = 1 to nodeArraySorted.count do
			(
				in coordsys parent nodePosition = tempNodes[k].pos
				in coordsys parent tempNodeRotation = tempNodes[k].rotation
				nodeRotation = quat -tempNodeRotation.x -tempNodeRotation.y -tempNodeRotation.z tempNodeRotation.w
				in coordsys parent nodeScale = (tempNodes[k].scale.x + tempNodes[k].scale.y + tempNodes[k].scale.z)/3
				
				format "%\t%\t%\n" nodePosition.x nodePosition.y nodePosition.z to:target
				format "%\t%\t%\t%\n" nodeRotation.x nodeRotation.y nodeRotation.z nodeRotation.w to:target
				format "%\n" nodeScale to:target
			)
			if (j != frameCount) do (sliderTime += 1)
		)
		format "\n// exported with zteam animation exporter\n\n" to:target
		
		max tool animmode
		set animate off
		try (delete tempNodes)
		catch ()
		tempNodes = #()
		
		sliderTime = 0
	)
	
	fn exportSingleAnim target =
	(
		outputFile = createFile target
		flushInstances ()
		failed = indexNodes ()
		if not failed then (writeAnim outputFile)
		flushInstances ()
		try (close outputFile)
		catch ()
	)
	
	fn exportAllAnims =
	(
		try
		(
			messageStream = stringStream ""
			format "%" "Done." to:messageStream
			for i in animExportQueue.listItems where i.checked do
			(
				if (i.index != 1) then (valid = loadMaxFile i.tag quiet:true)
				else (valid = true)
				if valid then
				(
					if (saveMethod.state == 1) then
					(
						if (maxFilePath == "") then (dirPart = trimRight (getDir #scene) "\\")
						else (dirPart = trimRight maxFilePath "\\")
					)
					else (dirPart = trimRight saveDir "\\")
					if (maxFileName == "") then (namePart = "z_scene_animation")
					else (namePart = getFilenameFile maxFileName)
					typePart = i.listSubItems[1].text
					
					if ((getFiles (dirPart + "\\" + namePart + "." + typePart)).count < 1) then (savePath = (dirPart + "\\" + namePart + "." + typePart))
					else
					(
						suffix = 0
						while ((getFiles (dirPart + "\\" + namePart + suffix as string + "." + typePart)).count > 0) do (suffix += 1)
						savePath = (dirPart + "\\" + namePart + suffix as string + "." + typePart)
						
						format "\n\nAnimation #% had a conflicting filename.\n" i.index to:messageStream
						format "It was saved as %" (filenameFromPath savePath) to:messageStream
					)
					
					if ((maxFilePath == "") and (maxFileName == "")) then
					(
						if (saveMethod.state == 1) then
						(
							format "\n\nAnimation #% did not have an initial filepath.\n" i.index to:messageStream
							format "It was saved as % in %" (filenameFromPath savePath) (getFilenamePath savePath) to:messageStream
						)
						else
						(
							format "\n\nAnimation #% did not have an initial filename.\n" i.index to:messageStream
							format "It was saved as %" (filenameFromPath savePath) to:messageStream
						)
					)
						
				
					exportSingleAnim savePath
				)
			)
			messageBox (messageStream as string) title:"Done"
		)
		catch (messageBox "Export failed." title:"Failed")
	)
	
	fn adjustQueue =
	(
		if (animExportQueue.listItems.count > 8) then (animExportQueue.columnHeaders[1].width = 8750)
		else (animExportQueue.columnHeaders[1].width = 9175)
		checkedCount = 0
		for i in animExportQueue.listItems where i.checked do (checkedCount += 1)
		if (checkedCount > 1) then (exportAnim.caption = "Export Animations")
		else
		(
			exportAnim.caption = "Export Animation"
			if (checkedCount < 1) then (exportAnim.enabled = false)
			else (exportAnim.enabled = true)
		)
	)
	
	fn addQueueItem scenePath =
	(
		animExportQueue.listItems.add ()
		animExportQueue.listItems[animExportQueue.listItems.count].tag = scenePath
		animExportQueue.listItems[animExportQueue.listItems.count].text = getFilenameFile scenePath
		animExportQueue.listItems[animExportQueue.listItems.count].checked = true
		animExportQueue.listItems[animExportQueue.listItems.count].listSubItems.add ()
		animExportQueue.listItems[animExportQueue.listItems.count].listSubItems[1].text = (substring animType.selected 1 3)
		animExportQueue.listItems[animExportQueue.listItems.count].listSubItems[1].tag = animType.selection
		adjustQueue ()
	)
	
	fn removeQueueItemsUnchecked =
	(
		for i in animExportQueue.listItems where (not i.checked and (i.index != 1)) do (animExportQueue.listItems.remove i.index)
		adjustQueue ()
	)
	
	fn addFile =
	(
		scenePath = getOpenFileName	caption:"Add MAX Scene" \
									filename:lastPath \
									types:"MAX Scene (*.MAX)|*.MAX|"
		if (scenePath != undefined) then (addQueueItem scenePath)
	)
	
	fn addDir =
	(
		sceneDir = getSavePath caption:"Add MAX Scenes from Directroy" initialDir:lastPath
		if (sceneDir != undefined) then
		(
			scenePaths = getFiles (sceneDir + "\\*.MAX")
			for i in scenePaths do (addQueueItem i)
		)
	)
	
	fn clearSaveDir =
	(
		saveDir = undefined
		saveDirText.text = ""
		saveDirClear.enabled = false
	)
	
	fn pickSaveDir =
	(
		clearSaveDir ()
		saveDir = getSavePath caption:"Pick Output File Directory" initialDir:lastPath
		if (saveDir != undefined) then
		(
			saveDirText.text = saveDir
			saveDirClear.enabled = true
		)
		else (clearSaveDir ())
	)
	
	fn populateQueue =
	(
		animExportQueue.checkboxes = true
		animExportQueue.fullRowSelect = true
		animExportQueue.gridLines = true
		animExportQueue.appearance = #ccFlat
		animExportQueue.view = #lvwReport
		animExportQueue.labelEdit = #lvwManual
		animExportQueue.columnHeaders.add ()
		animExportQueue.columnHeaders[1].text = "Queue"
		animExportQueue.columnHeaders[1].width = 9175
		animExportQueue.columnHeaders.add ()
		animExportQueue.columnHeaders[2].text = "Type"
		animExportQueue.columnHeaders[2].width = 1000
		addQueueItem "Current Scene Animation"
	)
	
	on animExporter open do
	(
		populateQueue ()
	)
	on animRemoveUnchecked pressed do (removeQueueItemsUnchecked ())
	on animAddFile pressed do (addFile ())
	on animAddFolder pressed do (addDir ())
	on animExportQueue itemClick item do (animType.selection = item.listSubItems[1].tag)
	on animExportQueue itemCheck item do (adjustQueue ())
	on animType selected element do
	(
		animExporter.animExportQueue.selectedItem.listSubItems[1].text = (substring animType.selected 1 3)
		animExporter.animExportQueue.selectedItem.listSubItems[1].tag = element
	)
	on saveMethod changed state do
	(
		if (state == 1) then
		(
			saveDirPick.enabled = false
			saveDirClear.enabled = false
		)
		else
		(
			saveDirPick.enabled = true
			saveDirClear.enabled = (saveDir != undefined)
		)
	)
	on saveDirPick pressed do (pickSaveDir ())
	on saveDirClear pressed do (clearSaveDir ())
	on exportAnim pressed do (exportAllAnims ())
)

createDialog animExporter