""" Meta data for provenance and version tracking in pymrio
"""

import datetime
import json
import logging
import os
import zipfile
from collections import OrderedDict
from pathlib import Path

from pymrio.core.constants import DEFAULT_FILE_NAMES


class MRIOMetaData(object):
    def __init__(
        self,
        location=None,
        description=None,
        name=None,
        system=None,
        version=None,
        path_in_arc="",
        logger_function=logging.info,
    ):

        """Organzises the MRIO meta data

        The meta data is stored in a json file.

        Note
        -----
            The parameters 'description', 'name', 'system', and
            'version' should be set during the establishment of the meta data
            file.  If the meta data file already exists and they are given
            again, the corresponding entry will be overwritten if
            replace_existing_meta_content is set to True (with a note in
            the 'History' field.)

        Parameters
        -----------

        location: str, valid path, optional
            Path or file for loading a previously saved metadata file and/or
            saving additional metadata (the method 'save' will use this
            location by default).  This can be the full file path or just the
            storage folder.  In the latter case, the filename defined in
            DEFAULT_FILE_NAMES['metadata'] (currently 'metadata.json') is
            assumed. The metadata can also be read from an archived zip file.
            In this case the data is 'read only' and can not be stored back
            to the same archive directly (writing data as zip archive not
            implemented yet). This means, that a new file has to be specified
            when saving the metadata.

        description: str, optional
            Description of the metadata file purpose and mrio,
            default set to 'Metadata file for pymrio'.
            Will be set the first time the metadata file gets established;
            subsequent changes are recorded in 'history'.

        name: str, optional
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

        path_in_arc: string, optional
            Path to the meta data in a zip file. path_in_arc must be given
            without leading dot or slash; thus to point to the data in the
            root of the compressed file pass '', for data in e.g. the folder
            'emissions' pass 'emissions/'.  Only used if parameter 'location'
            points to a compressed zip file.

        logger_function: func, optional
            Function accepting strings.
            The info string written to the metadata is also
            passed to this function. By default, the funtion
            is set to logging.info. Set to None for no output.

        """
        if location:
            location = Path(location)
            self._path_in_arc = None
            if location.is_file():
                self._metadata_file = location
                if zipfile.is_zipfile(str(location)):
                    with zipfile.ZipFile(file=str(location)) as zf:
                        if path_in_arc not in zf.namelist():
                            path_in_arc = os.path.join(
                                path_in_arc, DEFAULT_FILE_NAMES["metadata"]
                            )

                    self._path_in_arc = str(path_in_arc)

            elif location.is_dir():
                self._metadata_file = location / DEFAULT_FILE_NAMES["metadata"]
            else:
                if os.path.splitext(str(location))[1] == "":
                    self._metadata_file = location / DEFAULT_FILE_NAMES["metadata"]
                else:
                    self._metadata_file = location
        else:
            self._metadata_file = None

        self.logger = logger_function if logger_function else lambda x: None

        if self._metadata_file and self._metadata_file.is_file():
            self._read_content()
            self.logger("Read metadata from {}".format(self._metadata_file))

            if zipfile.is_zipfile(str(self._metadata_file)):
                self._metadata_file = None
                self._path_in_arc = None

            if description:
                self.change_meta("description", description)
            if name:
                self.change_meta("name", name)
            if system:
                self.change_meta("system", system)
            if version:
                self.change_meta("version", version)

        else:
            if not description:
                description = "Metadata for pymrio"
            self._content = OrderedDict(
                [
                    ("description", description),
                    ("name", name),
                    ("system", system),
                    ("version", version),
                    ("history", []),
                ]
            )
            self.logger("Start recording metadata")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        nr_hist_lines_show = 10

        hist = "\n".join(self._content["history"][:nr_hist_lines_show])

        if nr_hist_lines_show < len(self._content["history"]):
            hist = hist + "\n ... (more lines in history)"

        return (
            "Description: {desc}\n"
            "MRIO Name: {mrio}\n"
            "System: {system}\n"
            "Version: {ver}\n"
            "File: {metafile}\n"
            "History:\n{hist}".format(
                desc=self.description,
                mrio=self.name,
                system=self.system,
                ver=self.version,
                metafile=self._metadata_file,
                hist=hist,
            )
        )

    def note(self, entry):
        """Add the passed string as note to the history

        If log is True (default), also log the string by logging.info
        """
        self._add_history(entry_type="NOTE", entry=entry)

    def _add_fileio(self, entry):
        """ Add the passed string as FILEIO to the history """
        self._add_history(entry_type="FILEIO", entry=entry)

    def _add_modify(self, entry):
        """ Add the passed string as MODIFICATION to the history """
        self._add_history(entry_type="MODIFICATION", entry=entry)

    def _add_history(self, entry_type, entry):
        """ Generic method to add entry as entry_type to the history """
        meta_string = "{time} - {etype} -  {entry}".format(
            time=self._time(), etype=entry_type.upper(), entry=entry
        )

        self._content["history"].insert(0, meta_string)
        self.logger(meta_string)

    @property
    def metadata(self):
        return self._content

    @property
    def history(self):
        """ All recorded history """
        return self._content["history"]

    @property
    def modification_history(self):
        """ All modification history entries """
        return self._get_history_type("MODIFICATION")

    @property
    def note_history(self):
        """ All note history entries """
        return self._get_history_type("NOTE")

    @property
    def file_io_history(self):
        """ All fileio history entries """
        return self._get_history_type("FILEIO")

    def _get_history_type(self, history_type):
        return [ent for ent in self._content["history"] if history_type.upper() in ent]

    @property
    def description(self):
        return self._content["description"]

    @property
    def name(self):
        return self._content["name"]

    @property
    def system(self):
        return self._content["system"]

    @property
    def version(self):
        return self._content["version"]

    def change_meta(self, para, new_value, log=True):
        """Changes the meta data

        This function does nothing if None is passed as new_value.
        To set a certain value to None pass the str 'None'

        Parameters
        ----------
        para: str
            Meta data entry to change

        new_value: str
            New value

        log: boolean, optional
            If True (default) records the meta data change
            in the history

        """
        if not new_value:
            return
        para = para.lower()
        if para == "history":
            raise ValueError('History can only be extended - use method "note"')
        old_value = self._content.get(para, None)
        if new_value == old_value:
            return
        self._content[para] = new_value
        if old_value and log:
            self._add_history(
                entry_type="METADATA_CHANGE",
                entry='Changed parameter "{para}" '
                'from "{old}" to "{new}"'.format(
                    para=para, old=old_value, new=new_value
                ),
            )

    def _time(self):
        return "{:%Y%m%d %H:%M:%S}".format(datetime.datetime.now())

    def _read_content(self):
        """Reads metadata from location (and path_in_arc if archive)

        This function is called during the init process and
        should not be used in isolation: it overwrites
        unsafed metadata.
        """
        if self._path_in_arc:
            with zipfile.ZipFile(file=str(self._metadata_file)) as zf:
                self._content = json.loads(
                    zf.read(self._path_in_arc).decode("utf-8"),
                    object_pairs_hook=OrderedDict,
                )
        else:
            with self._metadata_file.open("r") as mdf:
                self._content = json.load(mdf, object_pairs_hook=OrderedDict)

    def save(self, location=None):
        """Saves the current status of the metadata

        This saves the metadata at the location of the previously loaded
        metadata or at the file/path given in location.

        Specify a location if the metadata should be stored in a different
        location or was never stored before. Subsequent saves will use the
        location set here.

        Parameters
        ----------
        location: str, optional
            Path or file for saving the metadata.
            This can be the full file path or just the storage folder.
            In the latter case, the filename defined in
            DEFAULT_FILE_NAMES['metadata'] (currently 'metadata.json') is
            assumed.
        """
        if location:
            location = Path(location)
            if os.path.splitext(str(location))[1] == "":
                self._metadata_file = location / DEFAULT_FILE_NAMES["metadata"]
            else:
                self._metadata_file = location

        if self._metadata_file:
            with self._metadata_file.open(mode="w") as mdf:
                json.dump(self._content, mdf, indent=4)
        else:
            logging.error("No metadata file given for storing the file")

    def __call__(self, note=None):
        """Shortcut for showing and adding notes

        If called without parameters, prints a full description
        of the metadata. If 'note' is given, add note and prints
        content.
        """
        if note:
            self.note(entry=note)

        print(self.__str__())
