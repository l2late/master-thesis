%     Copyright (C) 2021  Mathias Hudoba de Badyn
% 
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
% 
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.

function [u] = getAHU(room_vec, u_ahu_vec, x, u, h_low, h_high, c_low, c_high, u_n_max, u_h_max, u_c_max)
%getThermo: does hysteresis loop for AHU
%does not do cooling, only heating, since the AHU in our example is
%designed for heating only. cooling is activated via projection
% u_rad_vec contains the indices of the radiators

% u_ahu_vec = [idx_u_AHU_n, idx_u_AHU_h, idx_u_AHU_c];

ind_n = u_ahu_vec(1);
ind_h = u_ahu_vec(2);
ind_c = u_ahu_vec(3);

u_on = zeros(length(u_ahu_vec),1);

% sanitize inputs by rounding out small values
for ii = 1:length(u)
    if abs(u(ii))<1E-4
        u(ii) =0;
    end
end

% check if AHU is on or off
for ii = 1:length(u_ahu_vec)
    ind = u_ahu_vec((ii));
    if u(ind) > 1E-4
        u_on(ii) = 1;
    end
end

% do hysteresis on average of room temp
x_avg = mean(x(room_vec));


% if heaters are on and temp is above max, turn off

if u_on(ind_h) == 1 && x_avg >= h_high
    % turn off heating
    u(ind_h) = 0;
    
end

% if heaters are off and temp is below min, turn on
% if u_on(ind_h) == 0 && x_avg <= h_high % original (seems wrong)
if u_on(ind_h) == 0 && x_avg <= h_low
    % turn on heating
    u(ind_h) = u_h_max;

    % turn on air flow
    u(ind_n) = u_n_max;
end

% if coolers are off and temp is above max, turn on

if u_on(ind_c) == 0 && x_avg >= c_high
    % turn on cooler
    u(ind_c) = u_c_max;
    
    % turn on air flow
    u(ind_n) = u_n_max;
end

if u_on(ind_c) == 1 && x_avg <= c_low
    % turn off cooler
    u(ind_c) = 0;

end


% if not heating or cooling, turn off air flow
if u_on(ind_c) == 0 && u_on(ind_h) == 0
    u(ind_n) = 0;
end



end
