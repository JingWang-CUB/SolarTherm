within examples;

model receivervalidation
  extends SolarTherm.Icons.ToDo;
  import SolarTherm.{Models,Media};
  import Modelica.SIunits.Conversions.from_degC;
  import SI = Modelica.SIunits;
  import nSI = Modelica.SIunits.Conversions.NonSIunits;
  import CN = Modelica.Constants;
  import CV = Modelica.SIunits.Conversions;
  import FI = SolarTherm.Models.Analysis.Finances;
  import Util = SolarTherm.Media.SolidParticles.CarboHSP_utilities;
  import Modelica.Math;
  import Modelica.Blocks;
  replaceable package Medium = SolarTherm.Media.SolidParticles.CarboHSP_ph "Medium props for Carbo HSP 40/70";
  // Design Condition
  //parameter SI.MassFlowRate m_in(fixed = false);
  parameter SI.Power P_gross_design = 100e6;
  parameter Real eff_block_design = 0.502;
  parameter Real SolarMultiple = 2.5;
  parameter Real T_out_design = from_degC(800);
  parameter Real T_in_design = from_degC(580.3);
  parameter Real T_amb_design = from_degC(10);
  parameter Real CR = 1200;
  parameter SI.HeatFlux dni_des = 800;
  parameter SI.Efficiency eta_rec_assumption = 0.88;
  parameter SI.HeatFlowRate Q_in(fixed = false);
  parameter SI.Length H_drop_design = 24.1064;
  Modelica.Fluid.Sources.FixedBoundary source(redeclare package Medium = Medium, T = T_in_design, nPorts = 1, p = 1e5, use_T = true, use_p = false) annotation(
    Placement(visible = true, transformation(origin = {60, -14}, extent = {{10, -10}, {-10, 10}}, rotation = 0)));
  Modelica.Fluid.Sources.FixedBoundary sink(redeclare package Medium = Medium, T = 300.0, d = 3300, nPorts = 1, p = 1e5, use_T = true) annotation(
    Placement(visible = true, transformation(extent = {{34, 22}, {14, 42}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sources.FixedHeatFlow Heat(Q_flow = Q_in, T_ref = 298.15) annotation(
    Placement(visible = true, transformation(origin = {-78, 44}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Sources.BooleanExpression Operation(y = true) annotation(
    Placement(visible = true, transformation(origin = {-78, -4}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Sources.RealExpression realExpression(y = T_amb_design) annotation(
    Placement(visible = true, transformation(origin = {-56, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  SolarTherm.Models.Fluid.Pumps.LiftSimple liftSimple(use_input = true) annotation(
    Placement(visible = true, transformation(origin = {22, -16}, extent = {{-16, -16}, {16, 16}}, rotation = 0)));
  SolarTherm.Models.CSP.CRS.Receivers.ParticleReceiver1D particleReceiver1D(C = CR, N = 30, dni_des = dni_des, fixed_geometry = true, test_mode = true, with_uniform_curtain_props = false, with_wall_conduction = true, H_drop_design = H_drop_design) annotation(
    Placement(visible = true, transformation(origin = {-25, 37}, extent = {{-17, -17}, {17, 17}}, rotation = 0)));
  Modelica.Blocks.Sources.RealExpression m_in(y = 1 + time) annotation(
    Placement(visible = true, transformation(origin = {75, 30}, extent = {{-23, -18}, {23, 18}}, rotation = 180)));
initial equation
  Q_in = P_gross_design / eff_block_design / eta_rec_assumption * SolarMultiple;
//m_in = P_gross_design / eff_block_design / eta_rec_assumption * SolarMultiple / (Util.h_T(T_out_design) - Util.h_T(T_in_design));
equation
/*connect(Operation.y, receiver.on) H_drop
		annotation(
		Line(points = {{-69, -4}, {-39.5, -4}, {-39.5, 5}, {-25, 5}}, color = {255, 0, 255}));*/
  connect(source.ports[1], liftSimple.fluid_a) annotation(
    Line(points = {{50, -14}, {27, -14}}, color = {0, 127, 255}));
  connect(Heat.port, particleReceiver1D.heat) annotation(
    Line(points = {{-68, 44}, {-42, 44}, {-42, 42}, {-42, 42}}, color = {191, 0, 0}));
  connect(realExpression.y, particleReceiver1D.Tamb) annotation(
    Line(points = {{-44, 80}, {-26, 80}, {-26, 50}, {-24, 50}}, color = {0, 0, 127}));
  connect(particleReceiver1D.fluid_b, sink.ports[1]) annotation(
    Line(points = {{-20, 46}, {14, 46}, {14, 32}, {14, 32}}, color = {0, 127, 255}));
  connect(liftSimple.fluid_b, particleReceiver1D.fluid_a) annotation(
    Line(points = {{16, -14}, {-22, -14}, {-22, 22}, {-22, 22}}, color = {0, 127, 255}));
  connect(Operation.y, particleReceiver1D.on) annotation(
    Line(points = {{-66, -4}, {-28, -4}, {-28, 22}, {-28, 22}}, color = {255, 0, 255}));
  connect(m_in.y, liftSimple.m_flow) annotation(
    Line(points = {{50, 30}, {38, 30}, {38, 2}, {24, 2}, {24, -4}, {24, -4}}, color = {0, 0, 127}));
protected
  annotation(
    uses(Modelica(version = "3.2.2"), SolarTherm(version = "0.2")),
    experiment(StartTime = 0, StopTime = 2000, Tolerance = 1e-06, Interval = 1),
    __OpenModelica_simulationFlags(lv = "LOG_STATS", outputFormat = "mat", s = "dassl"),
    Diagram);
end receivervalidation;