from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True)

    lgd_code = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    name = Column(
        String,
        index=True,
        nullable=False
    )

    state_type = Column(
        String,
        index=True
    )

    districts = relationship(
        "District",
        back_populates="state"
    )


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True)

    lgd_code = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    name = Column(
        String,
        index=True,
        nullable=False
    )

    state_id = Column(
        Integer,
        ForeignKey("states.id"),
        nullable=False
    )

    state = relationship(
        "State",
        back_populates="districts"
    )

    subdistricts = relationship(
        "SubDistrict",
        back_populates="district"
    )


class SubDistrict(Base):
    __tablename__ = "subdistricts"

    id = Column(Integer, primary_key=True)

    lgd_code = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    name = Column(
        String,
        index=True,
        nullable=False
    )

    district_id = Column(
        Integer,
        ForeignKey("districts.id"),
        nullable=False
    )

    district = relationship(
        "District",
        back_populates="subdistricts"
    )

    places = relationship(
        "Place",
        back_populates="subdistrict"
    )


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)

    lgd_code = Column(
        String,
        unique=True,
        index=True
    )

    name = Column(
        String,
        index=True,
        nullable=False
    )

    place_type = Column(
        String,
        index=True
    )

    subdistrict_id = Column(
        Integer,
        ForeignKey("subdistricts.id"),
        nullable=False
    )

    subdistrict = relationship(
        "SubDistrict",
        back_populates="places"
    )

    postal_codes = relationship(
        "PostalCode",
        back_populates="place"
    )


class PostalCode(Base):
    __tablename__ = "postal_codes"

    id = Column(Integer, primary_key=True)

    pincode = Column(
        String,
        index=True,
        nullable=False
    )

    post_office = Column(
        String,
        index=True
    )

    place_id = Column(
        Integer,
        ForeignKey("places.id"),
        nullable=False
    )

    place = relationship(
        "Place",
        back_populates="postal_codes"
    )


class LocalBody(Base):
    __tablename__ = "local_bodies"

    id = Column(Integer, primary_key=True)

    lgd_code = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    name = Column(
        String,
        index=True,
        nullable=False
    )

    body_type = Column(
        String,
        index=True
    )

    state_id = Column(
        Integer,
        ForeignKey("states.id"),
        nullable=False
    )

    district_id = Column(
        Integer,
        ForeignKey("districts.id")
    )


# Temporary prototype table.
# We will eventually remove this after the new
# location system is working.
class Location(Base):
    __tablename__ = "locations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    lgd_code = Column(
        String,
        unique=True,
        index=True
    )

    name = Column(
        String,
        index=True
    )

    location_type = Column(
        String,
        index=True
    )

    state_code = Column(
        String,
        index=True
    )

    state_name = Column(
        String,
        index=True
    )

    district_code = Column(
        String,
        index=True
    )

    district_name = Column(
        String,
        index=True
    )

    subdistrict_code = Column(
        String,
        index=True
    )

    subdistrict_name = Column(
        String,
        index=True
    )