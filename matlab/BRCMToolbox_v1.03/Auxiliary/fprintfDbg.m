

function fprintfDbg(lvl,varargin)
   % FPRINTFDBG Debug level (global variable) dependent fprintf() function.
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
   
   
   global g_debugLvl
   if isempty(g_debugLvl)
      g_debugLvl = 1;
   end
   % g_debugLvl = -1 all output silent
   % g_debugLvl = 0 any not specifically requested output is completely silent
   % g_debugLvl = 1 is only most important
   % g_debugLvl = 2 all messages
   if g_debugLvl >= lvl
      if length(varargin) == 1
         fprintf(varargin{1});
      else
         fprintf(varargin{:});
      end
   end
   
end
