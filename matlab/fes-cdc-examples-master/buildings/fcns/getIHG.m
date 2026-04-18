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

function [v_ihg, ihg] = getIHG(ihg_vec, ihg_area, wph, t_space, p_array, t, nPeople, len_v)
%getIHG: gets the number of people in each room, then calculates their
%internal heat gain per area (W/m^2)

% t_space is not the t_space of the simulation, rather that of the markov
% chain for occupancy


% set t to 24 hr clock

t = mod(t, 24);

% find time point in time array and get the corresponding pmf
[~, it] = min(abs(t-t_space));

pmf = p_array(:, it);

% sample from pmf and count people

v_ihg = zeros(len_v,1);

pplVec = zeros(length(ihg_vec)+1,1);

for jj = 1:nPeople
    
    test = rand;
    val = 0;

    for ii = 1:length(pmf)
        val = val + pmf(ii);
        if rand <=val
            % sample is here
            pplVec(ii) = pplVec(ii)+1;
            break
        end
    end
end


% compute heat gains


for ii = 1:length(ihg_vec)
    ind = ihg_vec(ii);
    v_ihg(ind) = pplVec(ii)*wph/ihg_area(ind);
    ihg(ii) = v_ihg(ind);
end
    


end

