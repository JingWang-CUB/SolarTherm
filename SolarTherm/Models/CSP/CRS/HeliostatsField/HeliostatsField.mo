within SolarTherm.Models.CSP.CRS.HeliostatsField;
model HeliostatsField
  extends Interfaces.Models.Heliostats;
  parameter nSI.Angle_deg lon=133.889 "Longitude (+ve East)" annotation(Dialog(group="System location"));
  parameter nSI.Angle_deg lat=-23.795 "Latitude (+ve North)" annotation(Dialog(group="System location"));
  parameter Integer n_h=1 "Number of heliostats" annotation(Dialog(group="Technical data"));
  parameter SI.Area A_h=4 "Heliostat's Area" annotation(Dialog(group="Technical data"));
  parameter Real he_av=0.99 "Heliostat availability" annotation(Dialog(group="Technical data"));
  replaceable model Optical =
      SolarTherm.Models.CSP.CRS.HeliostatsField.Optical.Constant
  constrainedby
    SolarTherm.Models.CSP.CRS.HeliostatsField.Optical.OpticalEfficiency
    "Total optical efficency"
    annotation (Dialog(group="Technical data",__Dymola_label="nu"), choicesAllMatching=true);
  parameter Boolean use_on = false
    "= true to display when solar field is connected"
      annotation (Dialog(group="Operating strategy"), Evaluate=true, HideResult=true, choices(checkBox=true));
  parameter Boolean use_defocus = false "= true to use defocus strategy"
      annotation (Dialog(group="Operating strategy"), Evaluate=true, HideResult=true, choices(checkBox=true));
  parameter Boolean use_wind = false "= true to use Wind-stop strategy"
      annotation (Dialog(group="Operating strategy"), Evaluate=true, HideResult=true, choices(checkBox=true));
  parameter SI.Angle ele_min=from_deg(8) "Heliostat stow deploy angle" annotation(min=0,Dialog(group="Operating strategy"));
  parameter SI.HeatFlowRate Q_design=529.412 "Receiver design thermal power (with heat losses)" annotation(min=0,Dialog(group="Operating strategy"));
  parameter Real nu_start=0.60 "Receiver energy start-up fraction" annotation(min=0,Dialog(group="Operating strategy"));
  parameter Real nu_min=0.25 "Minimum receiver turndown energy fraction" annotation(min=0,Dialog(group="Operating strategy"));
  parameter Real nu_defocus=1 "Receiver limiter energy fraction at defocus state" annotation(Dialog(group="Operating strategy",enable=use_defocus));
  parameter SI.Velocity Wspd_max=15 "Wind stow speed" annotation(min=0,Dialog(group="Operating strategy",enable=use_wind));

  parameter SI.Energy E_start=90e3 "Start-up energy of a single heliostat" annotation(Dialog(group="Parasitic loads"));
  parameter SI.Power W_track=0.055e3 "Tracking power for a single heliostat" annotation(Dialog(group="Parasitic loads"));

  Optical optical(hra=solar.hra, dec=solar.dec, lat=lat);
  SI.HeatFlowRate Q_rec_inc_max;
  SI.HeatFlowRate Q_rec_inc;
  SI.HeatFlowRate Q_cos;
  SI.HeatFlowRate Q_ref;
  SI.HeatFlowRate Q_sb;
  SI.HeatFlowRate Q_att;
  SI.HeatFlowRate Q_spi;
  SI.HeatFlowRate Q_avail;

  Modelica.Blocks.Interfaces.BooleanOutput on if use_on annotation (Placement(
        transformation(extent={{-20,-20},{20,20}},
        rotation=-90,
        origin={0,-100}),                           iconTransformation(extent={{-12,-12},
            {12,12}},
        rotation=-90,
        origin={0,-100})));
  Modelica.Blocks.Interfaces.BooleanInput defocus if use_defocus annotation (Placement(
        transformation(extent={{-126,-88},{-86,-48}}),iconTransformation(extent={{-110,
            -72},{-86,-48}})));

  Modelica.Blocks.Interfaces.RealInput Wspd if use_wind annotation (Placement(
        transformation(extent={{-126,50},{-86,90}}), iconTransformation(extent={
            {-110,50},{-86,74}})));

  SI.Angle elo;
  SI.Angle ele;
  SI.Angle zen;
  SI.Angle zen2;
  SI.Angle azi;
  SI.Energy E_avail;
  SI.Energy E_rec_inc;
  //SI.Energy E_raw "including dumping loss"; 
  SI.Energy E_cos "Accumulated breakdown losses";
  SI.Energy E_ref;
  SI.Energy E_sb;
  SI.Energy E_att;
  SI.Energy E_spi;
  SI.Energy E_inc;
  SI.Energy E_defocus_load;
  SI.Energy E_optic_loss;
  
  SI.HeatFlowRate Q_field_HX_max;
  SI.HeatFlowRate Q_defocus_load;
  SI.HeatFlowRate Q_optic_loss;
  
  SI.Power W_loss;
  Real damping;
//protected
  Boolean on_hf;
protected
  SI.Power W_loss1;
  SI.Power W_loss2;
  //SI.Time t_start=30*60;
  parameter SI.Time t_start=3600 "Start-up traking delay";
  discrete Modelica.SIunits.Time t_on(start=0, fixed=true) "Sunrise time instant";
  Modelica.Blocks.Interfaces.BooleanInput on_internal
    "Needed to connect to conditional connector";
  Modelica.Blocks.Interfaces.BooleanInput defocus_internal
    "Needed to connect to conditional connector";
  Modelica.Blocks.Interfaces.RealInput Wspd_internal
    "Needed to connect to conditional connector";
  parameter SI.HeatFlowRate Q_start=nu_start*Q_design "Heliostat field start power" annotation(min=0,Dialog(group="Operating strategy"));
  parameter SI.HeatFlowRate Q_min=nu_min*Q_design "Heliostat field turndown power" annotation(min=0,Dialog(group="Operating strategy"));
  parameter SI.HeatFlowRate Q_field_PB_inc=nu_defocus*Q_design "Heat flow rate limiter at defocus state" annotation(Dialog(group="Operating strategy",enable=use_defocus));
  //parameter SI.HeatFlowRate Q_curtail=1e10 "Fixed heat flow rate for curtailment" annotation(min=0,Dialog(group="Operating strategy"));

initial equation
   on_internal=Q_rec_inc_max>Q_start;
equation
  if use_on then
    connect(on,on_internal);
  end if;
  if use_defocus then
    connect(defocus,defocus_internal);
  else
    defocus_internal = false;
  end if;
  if use_wind then
    connect(Wspd,Wspd_internal);
  else
    Wspd_internal = -1;
  end if;

  on_hf=(ele>ele_min) and
                     (Wspd_internal<Wspd_max);
  Q_rec_inc_max= if on_hf then max(he_av*n_h*A_h*solar.dni*optical.nu,0) else 0;
  Q_avail= if on_hf then max(he_av*n_h*A_h*solar.dni,0) else 0;
  
  when Q_rec_inc_max>Q_start then
    on_internal=true;
  elsewhen Q_rec_inc_max<Q_min then
    on_internal=false;
  end when;

  Q_rec_inc= if on_internal then (if defocus_internal then min(Q_field_PB_inc,Q_rec_inc_max) else min(Q_field_HX_max,Q_rec_inc_max)) else 0;
  Q_defocus_load= if on_hf then (if on_internal then (Q_rec_inc_max-Q_rec_inc)/optical.nu else Q_avail) else 0;
  Q_optic_loss=if on_internal then (Q_avail-Q_defocus_load-Q_rec_inc) else 0;
  Q_cos= if on_internal then max(Q_optic_loss*optical.nu_cos/(optical.nu_cos+optical.nu_ref+optical.nu_sb+optical.nu_att+optical.nu_spi),0) else 0;
  Q_ref= if on_internal then max(Q_optic_loss*optical.nu_ref/(optical.nu_cos+optical.nu_ref+optical.nu_sb+optical.nu_att+optical.nu_spi),0) else 0;
  Q_sb= if on_internal then max(Q_optic_loss*optical.nu_sb/(optical.nu_cos+optical.nu_ref+optical.nu_sb+optical.nu_att+optical.nu_spi),0) else 0;
  Q_att= if on_internal then max(Q_optic_loss*optical.nu_att/(optical.nu_cos+optical.nu_ref+optical.nu_sb+optical.nu_att+optical.nu_spi),0) else 0;
  Q_spi= if on_internal then max(Q_optic_loss*optical.nu_spi/(optical.nu_cos+optical.nu_ref+optical.nu_sb+optical.nu_att+optical.nu_spi),0) else 0;
  
  heat.Q_flow= -Q_rec_inc;
  elo=SolarTherm.Models.Sources.SolarFunctions.eclipticLongitude(solar.dec);
//   optical.hra=solar.hra;
//   optical.dec=solar.dec;

  ele=SolarTherm.Models.Sources.SolarFunctions.elevationAngle(
    solar.dec,
    solar.hra,
    lat);
  zen=pi/2-ele;
  zen2=SolarTherm.Models.Sources.SolarFunctions.aparentSolarZenith(
    solar.dec,
    solar.hra,
    lat);
  azi=SolarTherm.Models.Sources.SolarFunctions.solarAzimuth(
    solar.dec,
    solar.hra,
    lat);
  der(E_defocus_load) = Q_defocus_load;
  der(E_optic_loss) = Q_optic_loss;
  der(E_rec_inc) = Q_rec_inc;
  der(E_avail) = he_av*n_h*A_h*solar.dni;
  der(E_cos) = Q_cos;
  der(E_ref) = Q_ref;
  der(E_sb) = Q_sb;
  der(E_att) = Q_att;
  der(E_spi) = Q_spi;
  //der(E_raw) = Q_rec_inc_max;
  der(E_inc) = Q_avail;
  damping= if on_internal then Q_rec_inc/(Q_rec_inc_max+1e-3) else 1;
  W_loss1=if ele>1e-2 then n_h*he_av*damping*W_track else 0;
  when ele>1e-2 then
    t_on=time;
  end when;
  W_loss2= if time<t_on+t_start then n_h*he_av*damping*E_start/t_start else 0;
  W_loss=W_loss1+W_loss2;
  annotation (Documentation(info="<html>
</html>", revisions="<html>
<ul>
<li>Alberto de la Calle:<br>Released first version. </li>
</ul>
</html>"));
end HeliostatsField;
