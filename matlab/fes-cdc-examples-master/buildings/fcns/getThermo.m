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


function [u] = getThermo(room_vec, u_rad_vec, x, u, h_low, h_high, u_max)
%getThermo: does hysteresis loop
% u_rad_vec contains the indices of the radiators

u_on = zeros(size(u));

% check if heaters are on or off
for ii = 1:length(room_vec)
    ind = u_rad_vec((ii));
    if u(ind) > 0
        u_on(ii) = 1;
    end
end

% if heaters are on and temp is above max, turn off
for ii = 1:length(room_vec)
    ind_u = u_rad_vec(ii);
    ind_r = room_vec(ii);
    
    if u_on(ii) == 1 && x(ind_r) >= h_high
        u(ind_u) = 0;
    end
end

% if heaters are off and temp is below min, turn on
for ii = 1:length(room_vec)
    ind_u = u_rad_vec(ii);
    ind_r = room_vec(ii);
    
%     if u_on(ii) == 0 && x(ind_r) <= h_high % origininal (seems wrong)
    if u_on(ii) == 0 && x(ind_r) <= h_low
        u(ind_u) = u_max;
    end
end


end

