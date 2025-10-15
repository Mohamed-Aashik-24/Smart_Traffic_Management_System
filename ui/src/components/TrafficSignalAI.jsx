import React, { useState, useEffect } from 'react';
import { Camera, Car, Ambulance, TrendingUp, Clock, AlertTriangle } from 'lucide-react';

const TrafficSignalAI = () => {
  const [roads, setRoads] = useState([
    { id: 1, name: 'North Road', vehicles: 8, emergency: false, signal: 'red', timer: 30 },
    { id: 2, name: 'South Road', vehicles: 12, emergency: false, signal: 'green', timer: 25 },
    { id: 3, name: 'East Road', vehicles: 5, emergency: false, signal: 'red', timer: 30 },
    { id: 4, name: 'West Road', vehicles: 7, emergency: false, signal: 'red', timer: 30 }
  ]);
  const [currentActiveRoad, setCurrentActiveRoad] = useState(1);
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [cycleCount, setCycleCount] = useState(0);

  // ML Model Parameters
  const BASE_GREEN_TIME = 25; // Base green signal time in seconds
  const BASE_RED_TIME = 30; // Base red signal time in seconds
  const VEHICLE_WEIGHT = 2; // Seconds added per vehicle
  const EMERGENCY_PRIORITY_TIME = 40; // Green time for emergency vehicles
  const ADJUSTMENT_INCREMENT = 10; // Time adjustment for high traffic

  const calculateSignalTiming = (vehicleCount, hasEmergency) => {
    if (hasEmergency) {
      return {
        greenTime: EMERGENCY_PRIORITY_TIME,
        redTimeForOthers: BASE_RED_TIME + 15
      };
    }

    let greenTime = BASE_GREEN_TIME;
    if (vehicleCount > 10) {
      greenTime = BASE_GREEN_TIME + ADJUSTMENT_INCREMENT + (vehicleCount - 10) * VEHICLE_WEIGHT;
    } else if (vehicleCount > 6) {
      greenTime = BASE_GREEN_TIME + (vehicleCount - 6) * VEHICLE_WEIGHT;
    } else {
      greenTime = Math.max(15, BASE_GREEN_TIME - 5);
    }

    const redTimeForOthers = vehicleCount > 10 
      ? BASE_RED_TIME + ADJUSTMENT_INCREMENT 
      : BASE_RED_TIME;

    return { greenTime: Math.min(greenTime, 60), redTimeForOthers };
  };

  const calculateRoadPriority = (road) => {
    let score = road.vehicles * 10;
    if (road.emergency) score += 1000;
    score += (60 - road.timer) * 2;
    return score;
  };

  const selectNextRoad = () => {
    const priorities = roads.map(road => ({ ...road, priority: calculateRoadPriority(road) }));
    priorities.sort((a, b) => b.priority - a.priority);
    return priorities[0].id;
  };

  const addLog = (message, type = 'info') => {
    setLogs(prev => [{ time: new Date().toLocaleTimeString(), message, type }, ...prev].slice(0, 10));
  };

  const simulateVehicleDetection = () => {
    setRoads(prev => prev.map(road => ({ ...road, vehicles: Math.floor(Math.random() * 15) + 2, emergency: Math.random() > 0.9 })));
  };

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      setRoads(prev => {
        const updated = prev.map(road => {
          if (road.signal === 'green' && road.timer > 0) return { ...road, timer: road.timer - 1 };
          if (road.signal === 'red' && road.timer > 0) return { ...road, timer: road.timer - 1 };
          return road;
        });

        const activeRoad = updated.find(r => r.signal === 'green');
        if (activeRoad && activeRoad.timer === 0) {
          const nextRoadId = selectNextRoad();
          const nextRoad = updated.find(r => r.id === nextRoadId);
          const timing = calculateSignalTiming(nextRoad.vehicles, nextRoad.emergency);

          addLog(`Road ${nextRoad.name}: ${nextRoad.vehicles} vehicles${nextRoad.emergency ? ' + EMERGENCY' : ''} → Green: ${timing.greenTime}s`, nextRoad.emergency ? 'emergency' : 'success');

          setCycleCount(c => c + 1);

          return updated.map(road => {
            if (road.id === nextRoadId) return { ...road, signal: 'green', timer: timing.greenTime };
            return { ...road, signal: 'red', timer: timing.redTimeForOthers };
          });
        }

        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, roads]);

  useEffect(() => {
    if (!isRunning) return;
    const detectionInterval = setInterval(() => simulateVehicleDetection(), 8000);
    return () => clearInterval(detectionInterval);
  }, [isRunning]);

  const getSignalColor = (signal) => {
    switch(signal) {
      case 'green': return 'bg-green-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-slate-800 rounded-2xl p-6 mb-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                <Camera className="text-blue-400" size={32} />
                AI Traffic Signal Control System
              </h1>
              <p className="text-slate-400">ML-based adaptive signal timing with emergency vehicle priority</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">Signal Cycles</div>
              <div className="text-3xl font-bold text-blue-400">{cycleCount}</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-2xl p-6 mb-6 border border-slate-700">
          <div className="flex gap-4 items-center">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${isRunning ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white'}`}>
              {isRunning ? 'Stop System' : 'Start System'}
            </button>
            <button
              onClick={simulateVehicleDetection}
              disabled={isRunning}
              className="px-6 py-3 rounded-xl font-semibold bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Detect Vehicles
            </button>
            <div className="flex-1" />
            <div className="flex items-center gap-2 text-slate-300">
              <Clock size={20} />
              <span className="font-mono">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {roads.map(road => {
            const timing = calculateSignalTiming(road.vehicles, road.emergency);
            return (
              <div key={road.id} className={`bg-slate-800 rounded-2xl p-6 border-2 transition-all ${road.signal === 'green' ? 'border-green-500 shadow-lg shadow-green-500/20' : 'border-slate-700'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white">{road.name}</h3>
                  <div className={`w-16 h-16 rounded-full ${getSignalColor(road.signal)} shadow-lg flex items-center justify-center text-2xl font-bold text-white`}>{road.timer}</div>
                </div>

                {road.emergency && (
                  <div className="mb-4 bg-red-500/20 border border-red-500 rounded-lg p-3 flex items-center gap-2">
                    <Ambulance className="text-red-400" size={24} />
                    <span className="text-red-400 font-semibold">EMERGENCY VEHICLE DETECTED</span>
                  </div>
                )}

                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-slate-300">
                    <Car size={20} />
                    <span>Vehicles Detected:</span>
                    <span className="font-bold text-white text-xl">{road.vehicles}</span>
                  </div>

                  <div className="flex items-center gap-3 text-slate-300">
                    <TrendingUp size={20} />
                    <span>Suggested Green Time:</span>
                    <span className="font-bold text-green-400">{timing.greenTime}s</span>
                  </div>

                  <div className="flex items-center gap-3 text-slate-300">
                    <Clock size={20} />
                    <span>Red Time for Others:</span>
                    <span className="font-bold text-red-400">{timing.redTimeForOthers}s</span>
                  </div>

                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Traffic Density</span>
                      <span>{road.vehicles > 10 ? 'High' : road.vehicles > 6 ? 'Medium' : 'Low'}</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div className={`h-2 rounded-full transition-all ${road.vehicles > 10 ? 'bg-red-500' : road.vehicles > 6 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${Math.min((road.vehicles / 15) * 100, 100)}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-slate-800 rounded-2xl p-6 mb-6 border border-slate-700">
          <h3 className="text-xl font-bold text-white mb-4">ML Model Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm">Base Green Time</div>
              <div className="text-2xl font-bold text-white">{BASE_GREEN_TIME}s</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm">High Traffic Adjustment</div>
              <div className="text-2xl font-bold text-white">+{ADJUSTMENT_INCREMENT}s</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm">Emergency Priority</div>
              <div className="text-2xl font-bold text-white">{EMERGENCY_PRIORITY_TIME}s</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm">Vehicle Weight</div>
              <div className="text-2xl font-bold text-white">+{VEHICLE_WEIGHT}s/vehicle</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-white mb-4">System Activity Log</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-slate-400 text-center py-4">Start the system to see activity logs</p>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className={`p-3 rounded-lg flex items-start gap-3 ${log.type === 'emergency' ? 'bg-red-500/20 border border-red-500' : log.type === 'success' ? 'bg-green-500/20 border border-green-500' : 'bg-slate-700/50'}`}>
                  {log.type === 'emergency' && <AlertTriangle className="text-red-400 flex-shrink-0" size={20} />}
                  <div className="flex-1">
                    <span className="text-slate-400 text-sm font-mono">[{log.time}]</span>
                    <span className="text-white ml-2">{log.message}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrafficSignalAI;
