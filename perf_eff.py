import pandas as pd
import numpy as np
import math
import scipy.integrate

# Patrucco, 21/11/2019
# Power/performance figures.

GASOLINE_DENSITY_KGL = 0.75 #kg/L
STOICHIOMETRIC_RATIO = 14.7
AIR_DENSITY = 1.2 #kg/m3
GASOLINE_SPEC_HEAT = 43.6 #MJ/kg, inferiore (oppure kJ/g)
DIESEL_SPEC_HEAT = 44.4


def raw_eff(rpo, rht):
	return rpo / rht

def mff2heat(mff, spec_heat = GASOLINE_SPEC_HEAT):
	return (mff) * spec_heat # KW

def raw_power(rfo, vel):
	vms = vel / 3.6
	rpo = rfo * vms
	return .001*rpo # kW

def raw_force(vel, acc, mass, cx, S, air_density = AIR_DENSITY, remove_subzero = False):
	ap = [_aeroforce(vel[i], acc[i], cx, S, air_density) for i in range(len(vel))]
	ip = [mass * acc[i] for i in range(len(acc))]
	out = [(ap[i] + ip[i]) for i in range(len(ap))]
	if remove_subzero:
		for i in range(len(out)):
			if out[i] < 0:
				out[i] = 0
	return out # [N]

def _aeroforce(v, a, cx, s, r):
	out = .5 * r * cx * s * (v ** 2)
	return out


def vel2acc(vel, time):
	vms = vel / 3.6
	vdi = np.diff(vms) #, prepend = 0)
	tdi = np.diff(time) #, prepend = 1)
	return np.append([0], (vdi / tdi)) # m/s2

def progr_cons_lt(maf, time):
	lsec = maf2lsec(maf)
	lcum = scipy.integrate.cumtrapz(lsec, time, initial = 0)
	return lcum

def inst_kml(vel, maf):
	lsec = maf2lsec(maf)
	kmsec = vel / 3600
	return kmsec / lsec

def vel2dist(vel, time):
	dist = scipy.integrate.cumtrapz(vel, time, initial = 0)
	return dist

def maf2lsec(maf):
	return mff2lsec(maf2mff(maf))

def maf2mff(maf):
	return maf / STOICHIOMETRIC_RATIO

def mff2lsec(mff):
	return (mff * .001) / GASOLINE_DENSITY_KGL # liters per second

