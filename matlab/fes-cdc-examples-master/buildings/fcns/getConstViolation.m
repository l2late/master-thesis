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

function [cVio] = getConstViolation(t_space, x_array, xcon_array_min, xcon_array_max, room_vec)
%constraint violation: get in in degrees per hour

cVio = 0;

% do this with cumtrapz, the best function

zer = zeros(length(t_space),1);


    
for jj = 1:length(room_vec)
    ind = room_vec(jj);
    vio = max([ zer, xcon_array_min(ind,:)' - x_array(ind,:)', x_array(ind,:)' - xcon_array_max(ind,:)']');
    int = cumtrapz(t_space, vio);

    cVio = cVio + int(end);
end
    


end

