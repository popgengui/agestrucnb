'''
Description
manages output of the PGOpSimuPop object
based on Tiago Anteo's code in sim.py
'''
from builtins import range
from builtins import object
__filename__ = "pgoutputsimupop.py"
__date__ = "20160327"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import os
import bz2
import sys

#want to write genepop files
#to a temp name, then rename
#after writing is done:
import uuid

import shutil

import tempfile

FILE_DOES_NOT_EXIST=0
FILE_EXISTS_UNCOMPRESSED=1
FILE_EXISTS_AS_BZ2=2
FILE_EXISTS_AS_BOTH_UNCOMPRESSED_AND_BZ2=3

'''
2017_05_02. For python3, in def gen2Genepop(),
we need to decode the text read in from the compressed
*gen file.
'''
SYSDEFAULTENCODING=sys.getdefaultencoding()

'''
2017_03_20.  Until now the default way to join the alleles with the
individual id was simply to separate with a comma.  NeEstimator2 was
robust to this and correctly parsed.  However, now that we are also
using LDNe2 to get ldne estimates, it is necessary to put a space
after the comma, or the latter executable throws and error.  Also,
note that the comma plus space is the usual way to separate, and
though not specified in the file spec, it is the only way, now that
I've encountered the error, that other genepop files I've looked at
are formatted. We use a switch here in case there are any problems
with my code reading with the space, and I need to review changes.
'''
IN_POP_SECTIONS_SEPARATE_FIRST_LOCI_FROM_COMMA_WITH_SPACE=True

class PGOutputSimuPop( object ):
	'''
	Object meant to fetch parameter values and prepare them for 
	use in a simuPop simulation.  

	Object to be passed to a PGOpSimuPop object, which is, in turn,
	is passed to a PGGuiSimuPop object, or created in pgutilities,
	to run parallel replicates.  This object writes and manages the
	output of the simupop simulation. 

	2017_05_16.  Adding to the output file extensions the two files,
	listing age-counts and the PWOP Nb estimates file extensions.
	These are written by PGOpSimuPop instances, on the fist replicate
	only, initially to have been for testing only, but have become
	part of the standard output.  Their extensions are included here
	so that, if pgutilities def, remove_simulation_replicate_output_files
	is called on a cancelled simulation run, these files will also
	be removed.


	2017_08_08.  Adding to output file etendsions a file created when
	the new PGOpSimuPop.OUTPUT_GENEPOP_HET_FILTERED output mode is used.
	'''
	
	DICT_OUTPUT_FILE_EXTENSIONS={ "simfile":"sim",
									"genfile":"gen",
									"dbfile":"db",
									"conffile":"conf",
									"genepop":"genepop",
									"age_counts":"_age_counts_by_gen.tsv",
									"sim_nb_estimates":"_nb_values_calc_by_gen.tsv",
									"het_filter_info": "_het_value_by_cycle_number.tsv" }

	COMPRESSION_FILE_EXTENSION="bz2"

	def __init__( self, s_output_files_prefix ):

		self.__basename=s_output_files_prefix

		self.__set_file_names()

		self.out=None
		self.err=None
		self.megaDB=None
		self.conf=None
		'''
		2017_08_04.  Adding genepop as a member
		file name, after creating new output mode
		in class PGOpSimuPop, that writes only
		a genepop file.  Note that is mode will
		obviate any call to def gen2Genepop.
		'''
		self.genepop=None
		return
	#end def __init__
	
	def __set_file_names( self ):

		s_output_files_prefix=self.__basename

		self.__outname=s_output_files_prefix + "." \
				+ PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "simfile" ]
		self.__errname=s_output_files_prefix + "." \
				+ PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "genfile" ]
		self.__megadbname=s_output_files_prefix + "." \
				+ PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "dbfile" ]
		self.__confname=s_output_files_prefix + "." \
				+ PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "conffile" ]
		'''
		2017_08_04.  Adding the genepop file name to the member file names.
		This is to aid the use of new PGOpSimuPop output mode that writes
		genepop files only.
		'''
		self.__genepopname=s_output_files_prefix + "." \
				+ PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS[ "genepop" ]

		self.__genfile=self.__errname
		self.__simfile=self.__outname
		self.__dbfile=self.__megadbname
		self.__conffile=self.__confname
		self.__genepopfile=self.__genepopname

		return
	#end __set_file_names
	
	
	def __delete_file_names( self ):

		del self.__outname
		del self.__errname
		del self.__megadbname
		del self.__confname
		del self.__genepopname

		return
	#end __set_file_names
	
	def __file_exists(self, s_name):

		b_uncompressed_exists=os.path.isfile( s_name )
		b_compressed_exists=os.path.isfile( s_name + ".bz2" )

		if b_uncompressed_exists:
			if b_compressed_exists:
				return FILE_EXISTS_AS_BOTH_UNCOMPRESSED_AND_BZ2
			else:
				return FILE_EXISTS_UNCOMPRESSED
			#end if compressed else not
		else:
			if b_compressed_exists:
				return FILE_EXISTS_AS_BZ2
			else:
				return FILE_DOES_NOT_EXIST
			#end if b_compressed_exists
		#end if uncompressed else no uncompressed
		return b_exists
	#end __file_exists

	def __raise_file_exists_error( self, s_name, s_message=None ):
		#the likely problem is a simupop output file contained
		#in this object already exists:
		if s_message is None:
			s_message="In " + self.__mytype() + " instance, can't open file " \
				+ " for writing.  File, or its compressed version, " \
				+ s_name + ".bz2, " + " exists." 
		#end if default message
		raise Exception ( "In  " + self.__mytype() + " instance, file, " \
					+ s_name + " already exists.  " \
					+  "Failed operation: " + s_message )
	#end __raise_file_exists_error

	def __raise_file_not_found_error( self, s_name, s_failed_op ):
		raise Exception ( "In  " + self.__mytype() + " instance, file, " \
				+ s_name + " not found: caused failed operation: " \
				+ s_failed_op )
	#end __raise_file_not_found_error

	def openOut(self):
		if self.__file_exists( self.__outname ):
			self.__raise_file_exists_error( self.__outname )
		else:
			self.out=open( self.__outname, 'w' )
		#end if file exists, else open
		return
	#end openOut

	def openErr(self):
		if self.__file_exists( self.__errname ):
			self.__raise_file_exists_error( self.__errname )
		else:
			self.err=open( self.__errname, 'w' )
		#end if file exists, else open
		return
	#end openErr

	def openMegaDB(self):
		if self.__file_exists( self.__megadbname ):
			self.__raise_file_exists_error( self.__megadbname )
		else:
			self.megaDB=open( self.__megadbname, 'w' )
		#end if file exists, else open
		return
	#end openMegaDB

	'''
	2017_08_04 This def was added to facilitate the
	new output mode in PGOpSimupop code that writes
	only a genepop file, as pops are created.
	'''
	def openGenepop( self ):
		if self.__file_exists( self.__genepopname ):
			self.__raise_file_exists_error( self.__genepopname )
		else:
			self.genepop=open( self.__genepopname, 'w' )
		#end if file exists esle error
		return
	#end openGenepop
	
	def copyMe( self ):
		o_copy=PGOutputSimuPop( self.__basename )
		return o_copy
	#end copyMe

	def openConf(self):
		if self.__file_exists( self.__confname ):
			self.__raise_file_not_found_error( self.__confname )
		else:
			self.conf=open( self.__confname, 'w' )
		#end if file exists, else open
	#end openConf

	def bz2CompressAllFiles(self, ls_files_to_skip=[] ):
		'''
		used code and advice in, 
		http://stackoverflow.com/questions/9518705/big-file-compression-with-python

		Note: checked the shutil documentation at https://docs.python.org/2/library/shutil.html
		which warns of loss of meta file info (owner/group ACLs) when using shutil.copy() or shutil.copy2().  Unclear
		whether this applies to the copyfileobj, though my few tests showd all of these were retained.
		'''
		for s_myfile in [ self.__outname, self.__errname, self.__megadbname, self.__confname, self.__genepopname ]:
			
			if s_myfile in ls_files_to_skip:
				pass
			elif not self.__file_exists( s_myfile ):
				self.__raise_file_not_found_error( s_myfile, "compress file with bz2"  )
			else:
				with open( s_myfile, 'rb' ) as o_input:
					with bz2.BZ2File( s_myfile + '.bz2', 'wb', compresslevel=9 ) as o_output:
						#try/except overkill, but want logic to show
						#we don't remove the input file
						#if the copy op fails:
						try: 
							shutil.copyfileobj( o_input, o_output )
						except Exception as  e:
							raise e
						#end try except

						#required by windows only, else error can't remove:
						o_input.close()
						os.remove( s_myfile )	
					#end with bzfile for writing
				#end with current file for reading
			#end if file absent, else exists
		#end for each file
	#end bz2CompressAllFiles

	def writeGenepopFileHeaderAndLociList( self, 
								o_genepopfile,
								i_num_loci,
								f_nbne_ratio = None, 
								b_do_compress=False ):
	
		'''
		2017_08_04. Code to write the genpop file header
		and loci list was moved here from def gen2Genepop
		so that it can also be called from a PGOpSimuPop object
		that is writing the genepop file using the new
		mode that skips the intermediate *.gen, *.sim , etc.
		files.
		'''

		#write header and loci list:
		s_header="genepop from simupop sim run, data file " + self.__genfile

		if f_nbne_ratio is not None:
			s_header += ", nbne=" + str( f_nbne_ratio )
		#end if caller passed and nb/ne ratio value

		s_header_line=s_header + "\n"

		if b_do_compress:
			s_header_line=s_header_line.encode( SYSDEFAULTENCODING )
		#end if writing compressed data

		o_genepopfile.write(  s_header_line )


		for i_locus in range( i_num_loci ):
			s_locus_name="l" + str(i_locus) + "\n" 

			if b_do_compress:
				s_locus_name=s_locus_name.encode( SYSDEFAULTENCODING )
			#end if do compress	

			o_genepopfile.write(s_locus_name )

		#end for each loci number

		return
	#end writeGenepopFileHeaderAndLociList

	#derived from Tiao's code in ne2.py:
	def gen2Genepop( self, idx_allele_start, idx_allele_stop, 
			b_do_compress=True, 
			b_pop_per_gen=False,
			f_nbne_ratio=None ):

		'''
		reads the *.gen file from the simuPop output
		and produces a genepop file based on the gen file

		param idx_allele_start: int, one-based index giving the
		item (loci) number of the first allele entry in the line of gen-file input
		Example, if the *gen file has 10 microsates and 40 SNPs, then its first
		10 allele entries (that follow the indiv number and the gneration number)
		will be the microsats, and the final 40 allele entries will be the SNPs
		If we wanted only the Microsats to be included in the gen file, then
		this param would be "1", and the idx_allele_stop value would be 10. 
		If we want both msats and snps, we'd give 1 and 50 for these params. 
		If we want only SNPs, wed enter 11 for start allele and 50 for stop.

		param idx_allele_stop: int, one-based index giving the
		item (loci) number of the last allele entry in the line of gen-file input

		param optional b_do_compress, if true, will bzip2 the output genepop file

		param optional b_pop_per_gen, if true, will insert a "Pop" line between the
		generations, as given by the 2nd field in the gen file

		2017_02_12.  In implementing a bias adjustment in the NeEstimator's ldne-based
		Nb estimates, calculated in pgdriveneestimator.py, We add to this def an arg 
		"f_nbne_ratio", defalut None.  If arg is non-None, we append to the header line 
		text, "nbne=str(f_nbne_ratio)". When the GUI interface for the Nb estimation reads
		in genepop files, it will check for they key=value string and then, if present,
		pass the value on to the calls that eventually invoke the pgdriveneestimator.
		'''

		o_genfile=None

		o_genepopfile=None
	
		'''
		2017_04_21.  We change the way we name the temp file, so that it will be written
		int he output base path, rather than the currdir. Note that we define the var
		here, but create the name just before using, as the check for duplicate file names,
		which is perfomred in the call to our new def __get_temp_file_name, 
		should be done just before we then open the file.
		'''
		s_temp_file_name=None
	
		s_genepop_filename=self.__genepopname	

		i_num_loci=(idx_allele_stop-idx_allele_start) + 1

		IDX_GEN_INDIV=0
		IDX_GEN_GENERATION=1
		IDX_FIRST_ALLELE=2

		i_genepop_already_exists=self.__file_exists( s_genepop_filename )

		if i_genepop_already_exists != FILE_DOES_NOT_EXIST:

			self.__raise_file_exists_error( s_genepop_filename, 
					"create genepop file from gen file" )
		#end if genepop file already exists

		i_genfile_exists=self.__file_exists( self.__genfile )
		
		#if we have the uncompressed version available
		#we use it:
		if i_genfile_exists == FILE_EXISTS_UNCOMPRESSED \
			or i_genfile_exists == FILE_EXISTS_AS_BOTH_UNCOMPRESSED_AND_BZ2:

			o_genfile=open( self.__genfile )

		elif i_genfile_exists == FILE_EXISTS_AS_BZ2:
			o_genfile=bz2.BZ2File( self.__genfile + ".bz2", mode='r' )
		else:
			self.__raise_file_not_found_error( self.__genfile, "convert gen file to genepop" )
		#end if uncompressed only or uncomp. and compressed, else compressed only, else no file

		s_temp_file_name=self.__get_temp_file_name()

		if b_do_compress == True:
			o_genepopfile=bz2.BZ2File( s_temp_file_name + '.bz2', 'w', compresslevel=9 ) 
		else:
			o_genepopfile=open( s_temp_file_name, 'w' )
		#end if compress else don't

		#write header and loci list:
		self.writeGenepopFileHeaderAndLociList( o_genepopfile, 
													i_num_loci, 
													f_nbne_ratio, 
													b_do_compress )
		
		#write indiv id and alleles, line by line:
		i_currgen=None

		for s_line in o_genfile:

			'''
			2017_05_02.  For python 3, because in a compressed file python 3 reads bytes
			instead of strings (despite opening bzw2 in in mode='r'), 
			we need to decode if we read in bytes.
			'''
			if type( s_line ) == bytes:
				s_line=s_line.decode( SYSDEFAULTENCODING )
			#end if type is bytes

			ls_line = s_line.rstrip().split(" ") 

			'''
			As of 2016_09_01, we are no longer typing the id as an int, since
			we changed the indiv id string that is written to the gen file,
			(see pgopsimupop.py def __outputAge )
			to be a (currenly semicolon) delimited list of the indiv age,sex,etc)
			'''
			
			s_id = ls_line[IDX_GEN_INDIV]

			i_gen = int(float(ls_line[IDX_GEN_GENERATION]))
			idx_first_allele_in_line=( idx_allele_start + IDX_FIRST_ALLELE ) - 1
			idx_last_allele_in_line=( idx_allele_stop  + IDX_FIRST_ALLELE ) - 1 
			ls_alleles = ls_line[ idx_first_allele_in_line : idx_last_allele_in_line + 1 ]

			if i_currgen is None or ( b_pop_per_gen == True and i_currgen != i_gen ):
				s_pop_line="pop\n"

				if b_do_compress:
						s_pop_line=s_pop_line.encode( SYSDEFAULTENCODING )
				#end if b_do_compress

				o_genepopfile.write( s_pop_line )
				i_currgen=i_gen

			#end if no curr gen or new gen and we write pop per gen
			
			'''
			2017_03_20.  Until now the default way to join the alleles with the
			individual id was simply to separate with a comma.  NeEstimator2 was
			robust to this and correctly parsed.  However, now that we are also
			using LDNe2 to get ldne estimates, it is necessary to put a space
			after the comma, or the latter executable throws and error.  Also,
			note that the comma plus space is the usual way to separate, and
			though not specified in the file spec, it is the only way, now that
			I've encountered the error, that other genepop files I've looked at
			are formatted.
			'''
			if IN_POP_SECTIONS_SEPARATE_FIRST_LOCI_FROM_COMMA_WITH_SPACE==True:
				s_delimit_indiv_from_loci=", "
			else:
				s_delimit_indiv_from_loci=","
			#end if we aret to separate first loci from indiv with comma and space

			s_this_entry=s_id + s_delimit_indiv_from_loci +  " ".join( ls_alleles ) + "\n" 
		
			if b_do_compress:
				s_this_entry=s_this_entry.encode( SYSDEFAULTENCODING )
			#end if writing compressed data

			o_genepopfile.write( s_this_entry )

		#end for each line in gen file

		o_genfile.close()
		o_genepopfile.close()

		s_final_name=s_temp_file_name.replace( s_temp_file_name, s_genepop_filename )

		#change to shutil.move from os.rename -- threw errors (in docker install) when
		#renaming across volumes:
		if b_do_compress:
			s_temp_file_name=s_temp_file_name + ".bz2"
			s_final_name=s_final_name + ".bz2"
		#end if we wrote a compressed file

		shutil.move( s_temp_file_name, s_final_name )

		return
	#end gen2Popgene

	def __remove_output_file( self, s_file ):
		os.remove( s_file )
		return
	#end __remove_output_file

	def removeOutputFileByExt( self, s_extension ):

		if s_extension not in list(PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS.values()):
			s_msg="In PGOutputSimupop instance, def removeOutputFileByExt, " \
					+ "unknown extension was passed as argument: " \
					+ s_extension + "." \
					+ "Valid extensions include, " \
					+ ", ".join( list(PGOutputSimuPop.DICT_OUTPUT_FILE_EXTENSIONS.values()) ) \
					+ "."
			raise Exception( s_msg )
		#end if unknown extension
	
		s_outfile_name=self.__basename + "." + s_extension

		i_exists_status_flag=self.__file_exists( s_outfile_name )

		ls_files_to_remove=[]	

		if i_exists_status_flag in [ FILE_EXISTS_UNCOMPRESSED, 
						FILE_EXISTS_AS_BOTH_UNCOMPRESSED_AND_BZ2 ]:
			ls_files_to_remove.append( s_outfile_name )
		#end if uncompressed file exists

		if i_exists_status_flag in [ FILE_EXISTS_AS_BZ2, 
					FILE_EXISTS_AS_BOTH_UNCOMPRESSED_AND_BZ2 ]:
			ls_files_to_remove.append( s_outfile_name + "." \
					+ PGOutputSimuPop.COMPRESSION_FILE_EXTENSION )
		#end if compressed file exists


		for s_file in ls_files_to_remove:
			self.__remove_output_file( s_file )
		#end for each file 

		return
	#end removeOuputFileByExt

	def __get_temp_file_name( self ):
		'''
		This def would have been unnecessary,
		given pgutilities has the code, but
		pgutilities imports this module.
		'''

		s_out_dir=os.path.dirname( self.__basename )
		s_temp_file_name=tempfile.mktemp( dir=s_out_dir )

		'''
		We standardize the path as unix.
		
		'''
		if  sys.platform.lower().startswith( "win" ):
			s_temp_file_name=s_temp_file_name.replace( "\\", "/" )
		#end if

		if os.path.exists( s_temp_file_name ):
			s_msg="In PGOutputSimuPop, def __get_temp_file_name, " \
						+ "the program cannot make the temp file with name: " \
						+ s_temp_file_name + ".  The file already exists"
			raise Exception( s_msg )
		#end if path exists

		return s_temp_file_name
	#end def __get_temp_file_name

	@property
	def basename( self ):
		return self.__basename
	#end getter basename

	@basename.setter
	def basename( self, s_basename ):
		self.__basename=s_basename
		self.__set_file_names()
		return
	#end setter basename

	def __mytype( self ):
		return ( type( self ).__name__ )
	#end __mytype

	@property 
	def confname( self ):
		return self.__confname
	#end property confname

	@property 
	def simname( self ):
		return self.__outname
	#end property genname

	@property 
	def genname( self ):
		return self.__errname
	#end property dbname

	@property 
	def dbname( self ):
		return self.__megadbname
	#end property confname

	@property
	def genepopname( self ):
		return self.__genepopname
	#end property genepopname

#end class

