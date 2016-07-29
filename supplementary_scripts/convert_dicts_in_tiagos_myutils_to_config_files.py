'''
Description
have dictionaries in tiago antao's untility module used for
sumulation models in his other code in his AgeStructureNe project
want to make them text files as I adapt his program to a more general
(and gui) framework
'''
__filename__ = "convert_dicts_in_tiagos_mytils_to_config_files.py"
__date__ = "20160325"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import sys
import os
from ConfigParser import ConfigParser

sys.path.append( "/home/ted/documents/source_code/python/others_code/tiago_antao/AgeStructureNe" )

import myUtils as modut

#stubbed in secition name for all
#of the values not entered as (sub)dictionaries
#(i.e. for which tiage had dictionaries
#under the main dicdtiohnary that has
#species names as keys
MAIN_SECTION_NAME="resources"

def mymain():

	ls_dict_names=[ "meta", "ages", "gammaAFemale", "gammaBFemale", "gammaAMale", "gammaBMale", 
			"survivalFemale", "survivalMale", "fecFemale", "fecMale" ]
	do_parsers={}

	for s_dictionary_name in ls_dict_names:

		d_curr_dict=getattr( modut, s_dictionary_name )
		
		for s_species_common_name in d_curr_dict:

			if s_species_common_name not in do_parsers:
				do_parsers[ s_species_common_name ]=ConfigParser()
				do_parsers[ s_species_common_name ].optionxform = str
				do_parsers[ s_species_common_name ].add_section( MAIN_SECTION_NAME )
			#end if new species common name

			o_parser_for_this_species=do_parsers[ s_species_common_name ]

			v_entry_for_this_species=d_curr_dict[ s_species_common_name ]  

			o_this_type=type( v_entry_for_this_species  )
			
			if  o_this_type==dict:
				o_parser_for_this_species.add_section( s_dictionary_name )
				for s_key in v_entry_for_this_species:
					o_parser_for_this_species.set( s_dictionary_name,  str( s_key ), str( v_entry_for_this_species[ s_key ] ) )
				#end for each dict key
			elif o_this_type==list:
				o_parser_for_this_species.set( MAIN_SECTION_NAME, s_dictionary_name, v_entry_for_this_species )
			elif o_this_type==int:
				o_parser_for_this_species.set( MAIN_SECTION_NAME, s_dictionary_name, str( v_entry_for_this_species ) )
			else:
				raise Exception( "unknown type, value in " + s_dictionary_name + " for species, " + s_species_common_name )
			#end if thep dict, else....
		#end for each species
	#end for each dict

	for s_species_common_name in do_parsers:
		s_conf_file_for_this_species_name = \
				s_species_common_name + ".resources.conf"
		if os.path.isfile( s_conf_file_for_this_species_name ):
			sys.stderr.write( "Can't write to file "  \
					+ s_conf_file_for_this_species_name \
					+ ", file exists" )
		else:
			o_file=open( s_conf_file_for_this_species_name, 'w' )
			o_parser_for_this_species=do_parsers[ s_species_common_name ]
			o_parser_for_this_species.write( o_file )
			o_file.close()
		#end if file exists, skip write, else write
	#end for each parser, by species name
#end mymain

if  __name__ == "__main__":
	mymain()
#end if main module
