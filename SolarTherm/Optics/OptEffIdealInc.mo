within SolarTherm.Optics;
block OptEffIdealInc "Concentrator with fixed incline that tracks sun azimuth"
	extends SolarTherm.Optics.OptEff;
	import SI = Modelica.SIunits;
	import nSI = Modelica.SIunits.Conversions.NonSIunits;
	import Modelica.SIunits.Conversions.from_deg;
	import Modelica.Math.cos;

	parameter nSI.Angle_deg alt_fixed = 45 "Fixed concentrator altitude";
equation
	for i in 1:nelem loop
		eff[i] = max(cos(from_deg(alt_fixed - wbus.alt))/nelem, 0);
	end for;
end OptEffIdealInc;
