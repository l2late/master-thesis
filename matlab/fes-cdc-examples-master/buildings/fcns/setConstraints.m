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

function [xCon] = setConstraints(room_vec, t, margin)
%setConstraints: sets the room constraints depending on what time it is

t_now = mod(t,24);

if t_now <=22 && t_now >= 6
    % daytime constraints
    
    T_min = 20 - margin;
    T_max = 20 + margin;
    
else
    % nighttime constraints
    
    T_min = 17 - margin;
    T_max = 17 + margin;
    
end

for ii = 1:length(room_vec)
    ind = room_vec(ii);

    xCon.T_min(ind) = T_min;
    xCon.T_max(ind) = T_max;
end



end

