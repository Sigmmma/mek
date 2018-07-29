fn write_uint16_be file intVal = (
	WriteByte file (intVal / 256)
	WriteByte file (mod intVal 256)
)

fn write_float_be file floatVal = (
	local pos = ftell file
	WriteFloat file floatVal
	fseek file pos #seek_set
	fflush file
	local byte0 = ReadByte file #unsigned
	local byte1 = ReadByte file #unsigned
	local byte2 = ReadByte file #unsigned
	local byte3 = ReadByte file #unsigned
	fseek file pos #seek_set
	WriteByte file byte3
	WriteByte file byte2
	WriteByte file byte1
	WriteByte file byte0
)
cameraTrackControlPoints = $'control_point*' as array

if (cameraTrackControlPoints.count == 0) then (
	messageBox "No control points detected! Name each point to export as 'control_pointXX' where XX is the point number."
) else (
	trakPath = getSaveFileName	caption:"Save Camera Track" filename:"C:\\" \
								types:"Camera Track Tag (*.camera_track)|*.camera_track|"
	if (trakPath != undefined) then (
		local trakFile = fopen trakPath "wb+"

		--* Write the header
		for b = 1 to 36 do ( WriteByte trakFile 0 )
		WriteString trakFile "trakMozz"
		WriteByte trakFile 0
		write_uint16_be trakFile 64
		for b = 1 to 8 do ( WriteByte trakFile 0 )
		write_uint16_be trakFile 2
		write_uint16_be trakFile 255
		WriteString trakFile "blam"
	
		--* Write the trak body
		for b = 1 to 5 do ( WriteByte trakFile 0 )
		write_uint16_be trakFile cameraTrackControlPoints.count
		for b = 1 to 40 do ( WriteByte trakFile 0 )

		--* Write the control points
		for c = 1 to cameraTrackControlPoints.count do (
			local cp = cameraTrackControlPoints[c]

			write_float_be trakFile (cp.position.x / 100.0)
			write_float_be trakFile (cp.position.y / 100.0)
			write_float_be trakFile (cp.position.z / 100.0)
			write_float_be trakFile -cp.rotation.x
			write_float_be trakFile -cp.rotation.y
			write_float_be trakFile -cp.rotation.z
			write_float_be trakFile cp.rotation.w
			for b = 1 to 32 do ( WriteByte trakFile 0 )
		)
		fclose trakFile
		messageBox ("Successfully exported " + 
					(cameraTrackControlPoints.count as string) +
					" camera track control points")
	)
)