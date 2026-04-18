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

function [dg] = softThreshold(x, Tmin, Tmax)
% softThreshold: outputs the gradient of 0.5*max(0, Tmin-x, x-Tmax)^2,
% which is the soft thresholding function.

% sanitize inputs
if Tmax < Tmin
    warning('Max temp constraint is smaller than min temp constraint')
end


if x >= Tmax
    dg = x - Tmax;
elseif x <= Tmin
    dg = x - Tmin;
else
    dg = 0;
end


end

