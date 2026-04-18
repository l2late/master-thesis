function [dx, y] = onezone_2R2C(t, x, u, p, varargin)
% x(1): T_air, x(2): T_mass
T_a = x(1);
T_m = x(2);

Q_h   = u(1);   % heater
T_amb = u(2);   % ambient
Q_sol = u(3);   % solar

C_a    = p(1);
C_m    = p(2);
R_oa   = p(3);
R_am   = p(4);
alpha_h = p(5);
alpha_s = p(6);

dTadt = ( (T_amb - T_a)/R_oa + (T_m - T_a)/R_am ...
          + alpha_h*Q_h + alpha_s*Q_sol ) / C_a;

dTmdt = ( (T_a - T_m)/R_am ) / C_m;

dx = [dTadt; dTmdt];
y  = T_a;
end