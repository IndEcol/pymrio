""" Meta data for provenance and version tracking in pymrio
"""

import datetime
import json
import os
import logging

from collections import OrderedDict


class MRIOMetaData(object):

    def __init__(self, storage_folder,
                 description=None,
                 mrio_name=None,
                 system=None,
                 version=None,
                 logger_function=logging.info,
                 METADATA_FILENAME='metadata.json'):

        """ Organzises the MRIO meta data

        The meta data is stored in a json file. 

        Note
        -----

            The parameters 'description', 'mrio_name', 'system', and
            'version' should be set during the establishment of the meta data
            file.  If the meta data file already exists and they are given
            again, the corresponding entry will be overwritten if 
            replace_existing_meta_content is set to True (with a note in
            the 'History' field.)

        Parameters
        -----------

        storage_folder: str, valid path
            Path to the mrio containing a metadata file name as given in
            the parameter 'METADATA_FILENAME'

        description: str, optional
            Description of the metadata file purpose and mrio,
            default set to 'Metadata file for pymrio'.
            Will be set the first time the metadata file gets established;
            subsequent changes are recorded in 'history'.

        mrio_name: str, optional
            Name of the mrio (e.g. wiod, exiobase)
            Will be set the first time the metadata file gets established;
            subsequent changes are recorded in 'history'.

        system: str, optional
            For example 'industry by industry', 'ixi', ...
            Will be set the first time the metadata file gets established;
            subsequent changes are recorded in 'history'.

        version: str, int, float, optional
            Version number
            Will be set the first time the metadata file gets established;
            subsequent changes are recorded in 'history'.

        METADATA_FILENAME: str, optional
            Name of the metadata file, default: metadata.json

        logger_function: func, optional
            Function accepting strings.
            The info string written to the metadata is also 
            passed to this function. By default, the funtion
            is set to logging.info. Set to None for no output.

        """
        self._storage_folder = storage_folder
        self._METADATA_FILENAME = METADATA_FILENAME
        self._metadata_file = os.path.abspath(
            os.path.join(storage_folder, METADATA_FILENAME))

        self.logger = logger_function if logger_function else lambda x: None

        if os.path.isfile(self._metadata_file):
            self._read_content()
            if description:
                self.change_meta('description', description)
            if mrio_name:
                self.change_meta('mrio_name', mrio_name)
            if system:
                self.change_meta('system', system)
            if version:
                self.change_meta('version', version)
            
        else:
            if not description:
                description = 'Metadata file for pymrio'
            self._content = OrderedDict([
                ('description', description),
                ('mrio_name', mrio_name),
                ('system', system),
                ('version', version),
                ('history', []),
                ])
            self.logger("Start recording metadata")

    def __repr__(self):
        return ("MRIOMetaData(storage_folder={}, "
                "METADATA_FILENAME={})".format(self._storage_folder,
                                               self._METADATA_FILENAME))

    def __str__(self):
        nr_hist_lines_show = 10

        hist = "\n".join(self._content['history'][:nr_hist_lines_show])

        if nr_hist_lines_show < len(self._content['history']):
            hist = hist + "\n ... (more lines in history)"

        return ("Description: {desc}\n"
                "MRIO Name: {mrio}\n"
                "System: {system}\n"
                "Version: {ver}\n"
                "File: {metafile}\n"
                "History:\n{hist}".format(desc=self.description,
                                          mrio=self.mrio_name,
                                          system=self.system,
                                          ver=self.version,
                                          metafile=self._metadata_file,
                                          hist=hist))

    def note(self, entry, log=True):
        """ Add the passed string as note to the history

        If log is True (default), also log the string by logging.info
        """
        self._add_history(entry_type='NOTE', entry=entry)

    def _add_fileio(self, entry, log=True):
        """ Add the passed string as FILEIO to the history """
        self._add_history(entry_type='FILEIO', entry=entry)

    def _add_modify(self, entry, log=True):
        """ Add the passed string as MODIFICATION to the history """
        self._add_history(entry_type='MODIFICATION', entry=entry)

    def _add_history(self, entry_type, entry, log=True):
        """ Generic method to add entry as entry_type to the history """
        meta_string = "{time} - {etype} -  {entry}".format(time=self._time(),
                                                           etype=entry_type.upper(),
                                                           entry=entry)
        self._content['history'].insert( 0, meta_string)
        self.logger(meta_string)

    @property
    def metadata(self):
        return self._content

    @property
    def history(self):
        return self._content['history']

    @property
    def modification_history(self):
        """ All modification history entries """
        return self._get_history_type('MODIFICATION')

    @property
    def note_history(self):
        """ All note history entries """
        return self._get_history_type('NOTE')

    @property
    def file_io_history(self):
        """ All fileio history entries """
        return self._get_history_type('FILEIO')

    def _get_history_type(self, history_type):
        return [ent for ent in self._content['history']
                if history_type.upper() in ent]

    @property
    def description(self):
        return self._content['description']

    @property
    def mrio_name(self):
        return self._content['mrio_name']

    @property
    def system(self):
        return self._content['system']

    @property
    def version(self):
        return self._content['version']

    def change_meta(self, para, new_value, log=True):
        if para == 'history':
            raise ValueError(
                "History can only be extended - use method 'note'")
        old_value = self._content[para]
        if new_value == old_value:
            return
        self._content[para] = new_value
        self._add_history(entry_type="METADATA_CHANGE",
                          entry="Changed parameter '{para}' "
                                "from '{old}' to '{new}'".format(
                                    para=para,
                                    old=old_value,
                                    new=new_value))

    def _time(self):
        return '{:%Y%m%d %H:%M:%S}'.format(datetime.datetime.now())

    def _read_content(self):
        with open(self._metadata_file, 'r') as mdf:
            self._content = json.load(mdf,
                                      object_pairs_hook=OrderedDict)

    def save(self, log=True):
        """ Saves the current status of the metadata """
        with open(self._metadata_file, 'w') as mdf:
            json.dump(self._content, mdf, indent=4)

    def __call__(self, note=None):
        """ Shortcut for showing and adding notes

        If called without parameters, prints a full description
        of the metadata. If 'note' is given, add note and prints
        content.
        """
        if note:
            self.note(entry=note)

        print(self.__str__())


def load_metadata(location):
    """ Loads metadata file from location

    If location is a path, assumes the filename
    'metadata.json'
    """

    if not os.path.exists(location):
        raise FileNotFoundError('Could not find {}'.format(location))

    if os.path.isfile(location):
        meta = MRIOMetaData(storage_folder=os.path.dirname(location),
                            METADATA_FILENAME=os.path.basename(location))
    else:
        meta = MRIOMetaData(storage_folder=location)

    meta._add_fileio(
        'Load metadata file from {} without IO data'.format(location))

    return meta
