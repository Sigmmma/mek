import cProfile
from traceback import format_exc
from copy import copy
try:
    from reclaimer.gdl.handler import GdlHandler

    commands = ('i','g','o','a','d','t','ow','mips','alpha','all')
    all_cmd = set(commands)
    all_cmd.remove('ow')
    all_cmd.remove('all')

    test = GdlHandler(debug=3, valid_def_ids='objects', print_test=False)
    inp = ''
    inp = input('Type in extraction operators:\n\n'+
                '  d     == defs\n'+
                '  t     == textures\n'+
                '  g     == g3d models\n'+
                '  o     == obj models\n'+
                '  a     == animations\n'+
                '  all   == everything\n\n'+
                
                '  i     == individual models\n'+
                '  ow    == overwrite\n'+
                '  mips  == mipmaps\n'+
                '  alpha == alpha palette\n>>> ').lower().split(' ')
    cmd = set(c for c in commands if c in inp)
    if 'all' in cmd:
        cmd.update(all_cmd)
    
    while not cmd:
        inp = input('Type in extraction operators:\n>>> ').lower().split(' ')
        cmd = set(c for c in commands if c in inp)
        if 'all' in cmd:
            cmd.update(all_cmd)

    print('Loading tags. Please wait...')
    
    test.run_test()
    
    input('Hit enter when ready to rip.')
    
    for filepath in sorted(test.tags['objects']):
        print('extracting:', filepath)
        test.tags['objects'][filepath].extract_data(
            defs='d' in cmd, g3d='g' in cmd, obj='o' in cmd,
            tex='t' in cmd,  anim='a' in cmd, mips='mips' in cmd,
            individual='i' in cmd, alpha_pal='alpha' in cmd,
            overwrite='ow' in cmd)
        del test.tags['objects'][filepath]
        
    input('Extraction finished.')
except Exception:
    print(format_exc())
    input()
