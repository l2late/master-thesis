function r = getBRCMRootPath()
   % GETBRCMROOTPATH Returns the path where the BRCM_DemoFile.m is.
   % ------------------------------------------------------------------------
   % This file is part of the BRCM Toolbox v1.03.
   %
   % The BRCM Toolbox - Building Resistance-Capacitance Modeling for Model Predictive Control.
   % Copyright (C) 2013  Automatic Control Laboratory, ETH Zurich.
   % 
   % The BRCM Toolbox is free software; you can redistribute it and/or modify
   % it under the terms of the GNU General Public License as published by
   % the Free Software Foundation, either version 3 of the License, or
   % (at your option) any later version.
   % 
   % The BRCM Toolbox is distributed in the hope that it will be useful,
   % but WITHOUT ANY WARRANTY; without even the implied warranty of
   % MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   % GNU General Public License for more details.
   % 
   % You should have received a copy of the GNU General Public License
   % along with the BRCM Toolbox.  If not, see <http://www.gnu.org/licenses/>.
   %
   % For support check www.brcm.ethz.ch.
   % ------------------------------------------------------------------------
   
   
   w = which('BRCM_DemoFile.m','-all');
   if numel(w) == 0
      error('Could not find BRCM_DemoFile.m. Cannot determine BRCMRootPath');
   elseif numel(w)>1
      warning('Found too many BRCM_DemoFile.m. Use the first to determine BRCMRootPath');
      disp(w)
      w = w(1);
   end
   r = fileparts(w{1});
   
end
