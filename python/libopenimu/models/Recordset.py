"""
 Recordset
 @authors Simon Brière, Dominic Létourneau
 @date 05/04/2018
"""
from libopenimu.models.Base import Base
from libopenimu.models.Participant import Participant
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship


class Recordset(Base):
    __tablename__ = 'tabRecordsets'
    id_recordset = Column(Integer, Sequence('id_recordset_sequence'), primary_key=True, autoincrement=True)
    id_participant = Column(Integer, ForeignKey('tabParticipants.id_participant', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

    '''
    A type for datetime.timedelta() objects.
    The Interval type deals with datetime.timedelta objects. In PostgreSQL, the native INTERVAL type is used; 
    for others, the value is stored as a date which is relative to the “epoch” (Jan. 1, 1970).
    '''
    start_timestamp = Column(TIMESTAMP, nullable=False)
    end_timestamp = Column(TIMESTAMP, nullable=False)

    # Relationships
    participant = relationship("Participant")

    # Database rep (optional)
    def __repr__(self):
        return "<Recordset(id_participant='%s', name='%s', start_timestamp='%s', end_timestamp='%s'" % \
               (str(self.id_participant), str(self.name), str(self.start_timestamp), str(self.end_timestamp))


"""
from libopenimu.models.Participant import Participant


class Recordset:
    def __init__(self, *args, **kwargs):
        # Initialize from kwargs (and default values)
        self._id_recordset = kwargs.get('id_recordset', None)
        self._name = kwargs.get('name', None)
        self._participant = kwargs.get('participant', Participant())
        self._start_timestamp = kwargs.get('start_timestamp', 0)
        self._end_timestamp = kwargs.get('end_timestamp', 0)

        for arg in args:
            if isinstance(arg,tuple):
                self.from_tuple(arg)
            elif isinstance(arg, Recordset):
                self.from_tuple(arg.as_tuple())

    def __str__(self):
        return 'Recordset: ' + str(self.as_tuple())

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def get_id_recordset(self):
        return self._id_recordset

    def set_id_recordset(self, id_recordset):
        self._id_recordset = id_recordset

    def get_participant(self):
        return self._participant

    def set_participant(self, participant):
        self._participant = participant

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_start_timestamp(self):
        return self._start_timestamp

    def set_start_timestamp(self, start_timestamp):
        self._start_timestamp = start_timestamp

    def get_end_timestamp(self):
        return self._end_timestamp

    def set_end_timestamp(self, end_timestamp):
        self._end_timestamp = end_timestamp

    def as_tuple(self):
        return self._id_recordset, self._participant.as_tuple(), self._name, self._start_timestamp, self._end_timestamp

    def from_tuple(self, t):
        (self._id_recordset, participant_tuple, self._name, self._start_timestamp, self._end_timestamp) = t
        self._participant.from_tuple(participant_tuple)

    # Properties
    id_recordset = property(get_id_recordset, set_id_recordset)
    participant = property(get_participant, set_participant)
    name = property(get_name, set_name)
    start_timestamp = property(get_start_timestamp, set_start_timestamp)
    end_timestamp = property(get_end_timestamp, set_end_timestamp)
"""


