'''
Description
Tried several methods of using pythons multiprocessing module but could not
manage to instantiate simupop pops with independantly, randomly assigned gender.

This module was created to be called in a forked (subprocess.call)  os process,
 with stringigied args, then itself to build the args as 
 python structs and then to call the pgutilities def that builds a new simupop op 
 and runs the simulation:

				do_pgopsimupop_replicate_from_files(  s_configuration_file, 
												ls_life_table_files, 
												s_param_name_file, 
												s_outfile_basename, 
												i_replicate_number )


'''

__filename__ = "do_sim_replicate.py"
__date__ = "20160726"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import pgutilities as pgut

IDX_CONFIG_FILE=1
IDX_LIFE_TABLE_FILES=2
IDX_PARAM_FILE=3
IDX_OUTPUT_BASE_NAME=4
IDX_REPLICATE_NUMBER=5

DELIMITER_LIFE_TABLE_FILES=","

def destringify_args( s_life_table_files, s_replicate_number ):
	ls_life_table_files = s_life_table_files.split( DELIMITER_LIFE_TABLE_FILES )
	i_replicate_number=int( s_replicate_number )
	return ( ls_life_table_files, i_replicate_number )
#end sringify_args

def mymain( s_config_file, 
			s_life_table_files, 
			s_param_file, 
			s_output_base_name, 
			s_replicate_number ):

	ls_life_table_files, i_replicate_number = destringify_args( \
										s_life_table_files,
										s_replicate_number )
	
	pgut.do_pgopsimupop_replicate_from_files( s_config_file,
												ls_life_table_files,
												s_param_file,
												s_output_base_name,
												i_replicate_number )
	return
#end mymain

if __name__ == "__main__":

	ls_args=[ "config file name", 
				"comma-delmited list of file names, life tables",
				"parameter name file",
				"output base name",
				"int replicate number" ]

	s_usage = pgut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit(1)
	#end if s_usage

	s_config_file=sys.argv[ IDX_CONFIG_FILE ]
	s_life_table_files=sys.argv[ IDX_LIFE_TABLE_FILES ]
	s_param_file=sys.argv[ IDX_PARAM_FILE ]
	s_output_base_name=sys.argv[ IDX_OUTPUT_BASE_NAME ]
	s_replicate_number=sys.argv[ IDX_REPLICATE_NUMBER ]

	mymain( s_config_file,
				 s_life_table_files,
				 s_param_file,
				 s_output_base_name,
				 s_replicate_number )

#end if main

