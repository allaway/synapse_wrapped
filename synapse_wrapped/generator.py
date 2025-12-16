"""
Main generator for Synapse Wrapped visualizations.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

import pandas as pd

from synapse_wrapped.queries import (
    get_user_id_from_username,
    query_user_active_days,
    query_user_all_projects,
    query_user_collaboration_network,
    query_user_creations,
    query_user_files_downloaded,
    query_user_top_collaborators,
    query_user_top_projects,
    query_user_activity_by_date,
    query_user_creations_by_date,
    query_user_activity_by_month,
    query_user_activity_by_hour,
    query_user_time_patterns,
    query_user_first_download,
    query_user_busiest_day,
    query_user_largest_download,
    query_platform_average_file_size,
    query_user_average_file_size,
    query_user_monthly_download_size,
    query_platform_download_ranking,
    query_user_access_requirements,
)
from synapse_wrapped.utils import get_data_from_snowflake, close_all_sessions
from synapse_wrapped.visualizations import (
    create_active_days_card,
    create_creations_card,
    create_files_downloaded_card,
    create_network_card,
    create_projects_wordcloud_card,
    create_top_collaborators_card,
    create_top_projects_card,
)


def get_html_template() -> str:
    """Return the HTML template for the wrapped visualization - Spotify Wrapped style."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synapse Wrapped {year}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Exo+2:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root {
            --neon-cyan: #00fff7;
            --neon-magenta: #ff00ff;
            --neon-purple: #a855f7;
            --neon-pink: #ff6b9d;
            --neon-green: #00ffaa;
            --dark-bg: #0a0a0f;
            --dark-card: #12121a;
            --dark-card-border: #1e1e2e;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body {
            height: 100%;
            overflow: hidden;
        }
        
        body {
            font-family: 'Exo 2', sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
        }
        
        /* Animated background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            background: 
                radial-gradient(ellipse at 20% 80%, rgba(168, 85, 247, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(0, 255, 247, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(255, 0, 255, 0.05) 0%, transparent 70%),
                var(--dark-bg);
            animation: bgPulse 8s ease-in-out infinite alternate;
        }
        
        @keyframes bgPulse {
            0% { opacity: 1; }
            100% { opacity: 0.7; }
        }
        
        /* Floating particles */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
            overflow: hidden;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--neon-cyan);
            border-radius: 50%;
            opacity: 0.3;
            animation: float 20s infinite linear;
        }
        
        .particle:nth-child(2n) { background: var(--neon-magenta); animation-duration: 25s; }
        .particle:nth-child(3n) { background: var(--neon-purple); animation-duration: 30s; }
        
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 0.3; }
            90% { opacity: 0.3; }
            100% { transform: translateY(-100vh) rotate(720deg); opacity: 0; }
        }
        
        /* Grid overlay */
        .grid-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            background-image: 
                linear-gradient(rgba(0, 255, 247, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 247, 0.02) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
        }
        
        /* Slides container */
        .slides-container {
            position: relative;
            width: 100%;
            height: 100%;
            z-index: 2;
        }
        
        .slide {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
            padding-bottom: 100px;
            opacity: 0;
            transform: scale(0.95);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            overflow-y: auto;
        }
        
        .slide.active {
            opacity: 1;
            transform: scale(1);
            pointer-events: auto;
        }
        
        .slide.prev {
            opacity: 0;
            transform: translateX(-100%) scale(0.9);
        }
        
        .slide.next {
            opacity: 0;
            transform: translateX(100%) scale(0.9);
        }
        
        /* Slide content with staggered animations */
        .slide-content {
            max-width: 900px;
            width: 100%;
            text-align: center;
        }
        
        .slide.active .animate-in {
            animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        
        .slide.active .animate-in:nth-child(1) { animation-delay: 0.1s; }
        .slide.active .animate-in:nth-child(2) { animation-delay: 0.2s; }
        .slide.active .animate-in:nth-child(3) { animation-delay: 0.3s; }
        .slide.active .animate-in:nth-child(4) { animation-delay: 0.4s; }
        .slide.active .animate-in:nth-child(5) { animation-delay: 0.5s; }
        
        @keyframes slideUp {
            0% { opacity: 0; transform: translateY(40px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        .animate-in {
            opacity: 0;
        }
        
        /* Title slide */
        .title-slide .logo {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            color: var(--neon-cyan);
            letter-spacing: 0.3em;
            margin-bottom: 20px;
            text-transform: uppercase;
            animation: glitchText 4s infinite;
        }
        
        @keyframes glitchText {
            0%, 90%, 100% { text-shadow: none; }
            92% { text-shadow: -2px 0 var(--neon-magenta), 2px 0 var(--neon-cyan); }
            94% { text-shadow: 2px 0 var(--neon-magenta), -2px 0 var(--neon-cyan); }
            96% { text-shadow: -1px 0 var(--neon-magenta), 1px 0 var(--neon-cyan); }
        }
        
        .title-slide h1 {
            font-family: 'Orbitron', monospace;
            font-size: clamp(2.5rem, 8vw, 5rem);
            font-weight: 900;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            animation: titleGlow 3s ease-in-out infinite alternate;
        }
        
        @keyframes titleGlow {
            0% { filter: drop-shadow(0 0 20px rgba(0, 255, 247, 0.5)); }
            100% { filter: drop-shadow(0 0 40px rgba(168, 85, 247, 0.8)); }
        }
        
        .title-slide .year {
            font-family: 'Orbitron', monospace;
            font-size: clamp(4rem, 15vw, 10rem);
            font-weight: 900;
            color: var(--text-primary);
            line-height: 1;
            margin-bottom: 30px;
            text-shadow: 
                0 0 20px rgba(255, 255, 255, 0.3),
                0 0 40px rgba(0, 255, 247, 0.2);
            animation: yearPulse 2s ease-in-out infinite;
        }
        
        @keyframes yearPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
        
        .title-slide .username {
            font-size: 1.5rem;
            color: var(--neon-cyan);
            margin-bottom: 60px;
        }
        
        .start-btn {
            font-family: 'Orbitron', monospace;
            font-size: 1rem;
            padding: 18px 50px;
            background: transparent;
            border: 2px solid var(--neon-cyan);
            color: var(--neon-cyan);
            cursor: pointer;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .start-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 247, 0.4), transparent);
            animation: btnShine 3s infinite;
        }
        
        @keyframes btnShine {
            0% { left: -100%; }
            50%, 100% { left: 100%; }
        }
        
        .start-btn:hover {
            background: var(--neon-cyan);
            color: var(--dark-bg);
            box-shadow: 0 0 30px rgba(0, 255, 247, 0.5);
            transform: scale(1.05);
        }
        
        /* Metric slides */
        .metric-label {
            font-size: 1.2rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.3em;
            margin-bottom: 20px;
        }
        
        .metric-value {
            font-family: 'Orbitron', monospace;
            font-size: clamp(4rem, 18vw, 12rem);
            font-weight: 900;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
        }
        
        .slide.active .metric-value {
            animation: numberPop 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards, 
                       metricGlow 2s ease-in-out infinite 0.8s;
        }
        
        @keyframes numberPop {
            0% { transform: scale(0.5); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        @keyframes metricGlow {
            0%, 100% { filter: drop-shadow(0 0 20px rgba(0, 255, 247, 0.3)); }
            50% { filter: drop-shadow(0 0 40px rgba(168, 85, 247, 0.5)); }
        }
        
        .metric-unit {
            font-size: 1.5rem;
            color: var(--neon-magenta);
            margin-top: 10px;
            letter-spacing: 0.1em;
        }
        
        .metric-context {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-top: 30px;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Project list */
        .project-list, .collaborator-list {
            text-align: left;
            max-width: 700px;
            margin: 0 auto;
            max-height: 70vh;
            overflow-y: auto;
            padding-right: 10px;
        }
        
        .project-list::-webkit-scrollbar, .collaborator-list::-webkit-scrollbar {
            width: 6px;
        }
        
        .project-list::-webkit-scrollbar-track, .collaborator-list::-webkit-scrollbar-track {
            background: var(--dark-card);
            border-radius: 3px;
        }
        
        .project-list::-webkit-scrollbar-thumb, .collaborator-list::-webkit-scrollbar-thumb {
            background: var(--neon-cyan);
            border-radius: 3px;
        }
        
        .project-item {
            display: flex;
            align-items: center;
            padding: 16px 20px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.8), rgba(30, 30, 46, 0.6));
            border: 1px solid var(--dark-card-border);
            border-radius: 15px;
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateX(-30px);
        }
        
        .slide.active .project-item {
            animation: slideInLeft 0.5s ease forwards;
        }
        
        .slide.active .project-item:nth-child(1) { animation-delay: 0.1s; }
        .slide.active .project-item:nth-child(2) { animation-delay: 0.15s; }
        .slide.active .project-item:nth-child(3) { animation-delay: 0.2s; }
        .slide.active .project-item:nth-child(4) { animation-delay: 0.25s; }
        .slide.active .project-item:nth-child(5) { animation-delay: 0.3s; }
        .slide.active .project-item:nth-child(6) { animation-delay: 0.35s; }
        .slide.active .project-item:nth-child(7) { animation-delay: 0.4s; }
        .slide.active .project-item:nth-child(8) { animation-delay: 0.45s; }
        .slide.active .project-item:nth-child(9) { animation-delay: 0.5s; }
        .slide.active .project-item:nth-child(10) { animation-delay: 0.55s; }
        
        @keyframes slideInLeft {
            to { opacity: 1; transform: translateX(0); }
        }
        
        .project-item:hover {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 20px rgba(0, 255, 247, 0.2);
            transform: translateX(10px);
        }
        
        .project-rank {
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--neon-cyan);
            min-width: 50px;
            text-align: center;
        }
        
        .project-info {
            flex: 1;
            margin-left: 15px;
            min-width: 0;
        }
        
        .project-name {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .project-metric {
            font-size: 0.85rem;
            color: var(--neon-purple);
        }
        
        /* Collaborator list */
        .collaborator-item {
            display: flex;
            align-items: center;
            padding: 16px 20px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.8), rgba(30, 30, 46, 0.6));
            border: 1px solid var(--dark-card-border);
            border-radius: 15px;
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateX(-30px);
            cursor: pointer;
            text-decoration: none;
        }
        
        .collaborator-item.no-link {
            cursor: default;
        }
        
        .slide.active .collaborator-item {
            animation: slideInLeft 0.5s ease forwards;
        }
        
        .slide.active .collaborator-item:nth-child(1) { animation-delay: 0.1s; }
        .slide.active .collaborator-item:nth-child(2) { animation-delay: 0.15s; }
        .slide.active .collaborator-item:nth-child(3) { animation-delay: 0.2s; }
        .slide.active .collaborator-item:nth-child(4) { animation-delay: 0.25s; }
        .slide.active .collaborator-item:nth-child(5) { animation-delay: 0.3s; }
        .slide.active .collaborator-item:nth-child(6) { animation-delay: 0.35s; }
        .slide.active .collaborator-item:nth-child(7) { animation-delay: 0.4s; }
        .slide.active .collaborator-item:nth-child(8) { animation-delay: 0.45s; }
        .slide.active .collaborator-item:nth-child(9) { animation-delay: 0.5s; }
        .slide.active .collaborator-item:nth-child(10) { animation-delay: 0.55s; }
        
        .collaborator-item:hover {
            border-color: var(--neon-magenta);
            box-shadow: 0 0 20px rgba(255, 0, 255, 0.2);
            transform: translateX(10px);
        }
        
        .collaborator-item.no-link:hover {
            transform: translateX(0);
        }
        
        .collaborator-rank {
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--neon-magenta);
            min-width: 50px;
            text-align: center;
        }
        
        .collaborator-info {
            flex: 1;
            margin-left: 15px;
        }
        
        .collaborator-name {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .collaborator-metric {
            font-size: 0.85rem;
            color: var(--neon-purple);
        }
        
        .external-link-icon {
            color: var(--text-secondary);
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .collaborator-item:hover .external-link-icon {
            opacity: 1;
        }
        
        /* Wordcloud & network images */
        .wordcloud-img {
            max-width: 100%;
            height: auto;
            border-radius: 20px;
            margin-top: 30px;
            border: 1px solid var(--dark-card-border);
            box-shadow: 0 0 40px rgba(0, 255, 247, 0.1);
        }
        
        /* Interactive wordcloud */
        .slide-wordcloud .slide-content {
            padding-top: 80px;
        }
        
        .slide-wordcloud .metric-label {
            margin-top: 20px;
        }
        
        .slide-wordcloud .metric-value {
            font-size: clamp(2.8rem, 12.6vw, 8.4rem);
        }
        
        #wordcloud-container {
            width: 100%;
            max-width: 1000px;
            height: 500px;
            margin: 30px auto;
            position: relative;
        }
        
        .wordcloud-word {
            cursor: pointer;
            transition: all 0.3s ease;
            user-select: none;
            position: absolute;
        }
        
        .wordcloud-word:hover {
            transform: scale(1.2);
            z-index: 10;
            filter: drop-shadow(0 0 8px currentColor);
        }
        
        /* Interactive network */
        #network-container {
            width: 100%;
            max-width: 800px;
            height: 500px;
            margin: 20px auto;
            background: rgba(18, 18, 26, 0.8);
            border-radius: 20px;
            border: 1px solid var(--dark-card-border);
            overflow: hidden;
        }
        
        #network-container svg {
            width: 100%;
            height: 100%;
        }
        
        .network-node {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .network-node:hover {
            filter: brightness(1.3);
        }
        
        .network-link {
            stroke-opacity: 0.6;
        }
        
        .network-label {
            font-family: 'Exo 2', sans-serif;
            font-size: 10px;
            fill: white;
            pointer-events: none;
            text-shadow: 0 0 5px rgba(0,0,0,0.8);
        }
        
        .network-tooltip {
            position: absolute;
            background: rgba(18, 18, 26, 0.95);
            border: 1px solid var(--neon-cyan);
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 0.85rem;
            color: var(--text-primary);
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 0 20px rgba(0, 255, 247, 0.3);
        }
        
        /* Creation breakdown */
        .creation-breakdown {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 40px;
            flex-wrap: wrap;
        }
        
        .creation-item {
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.9), rgba(30, 30, 46, 0.7));
            border: 1px solid var(--dark-card-border);
            padding: 25px 35px;
            border-radius: 15px;
            text-align: center;
            min-width: 130px;
            opacity: 0;
            transform: translateY(20px);
        }
        
        .slide.active .creation-item {
            animation: fadeUp 0.6s ease forwards;
        }
        
        .slide.active .creation-item:nth-child(1) { animation-delay: 0.2s; }
        .slide.active .creation-item:nth-child(2) { animation-delay: 0.4s; }
        .slide.active .creation-item:nth-child(3) { animation-delay: 0.6s; }
        .slide.active .creation-item:nth-child(4) { animation-delay: 0.8s; }
        
        @keyframes fadeUp {
            to { opacity: 1; transform: translateY(0); }
        }
        
        .creation-count {
            font-family: 'Orbitron', monospace;
            font-size: 2rem;
            font-weight: 700;
            color: var(--neon-cyan);
        }
        
        .creation-type {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 8px;
        }
        
        /* Activity Heatmap */
        .heatmap-container {
            width: 100%;
            max-width: 900px;
            margin: 30px auto;
            padding: 20px;
            background: rgba(18, 18, 26, 0.8);
            border-radius: 20px;
            border: 1px solid var(--dark-card-border);
        }
        
        .heatmap-grid {
            display: flex;
            gap: 3px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .heatmap-month {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        
        .heatmap-month-label {
            font-size: 0.7rem;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 5px;
        }
        
        .heatmap-week {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        
        .heatmap-cell {
            width: 12px;
            height: 12px;
            border-radius: 2px;
            background: var(--dark-card);
            transition: all 0.2s ease;
        }
        
        .heatmap-cell:hover {
            transform: scale(1.5);
            box-shadow: 0 0 10px currentColor;
        }
        
        .heatmap-cell.level-1 { background: rgba(0, 255, 247, 0.2); }
        .heatmap-cell.level-2 { background: rgba(0, 255, 247, 0.4); }
        .heatmap-cell.level-3 { background: rgba(0, 255, 247, 0.6); }
        .heatmap-cell.level-4 { background: var(--neon-cyan); }
        
        .heatmap-legend {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 15px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        .heatmap-legend-cell {
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }
        
        /* Most active months */
        .active-months {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 30px;
        }
        
        .month-badge {
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.9), rgba(30, 30, 46, 0.7));
            border: 1px solid var(--neon-cyan);
            border-radius: 20px;
            padding: 12px 20px;
            text-align: center;
            min-width: 100px;
        }
        
        .month-badge.top {
            border-color: var(--neon-magenta);
            box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
        }
        
        .month-name {
            font-family: 'Orbitron', monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
        }
        
        .month-stat {
            font-size: 0.75rem;
            color: var(--neon-purple);
            margin-top: 5px;
        }
        
        /* Navigation */
        .nav-controls {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 100;
            padding: 15px 25px;
            background: rgba(10, 10, 15, 0.9);
            border-radius: 30px;
            border: 1px solid var(--dark-card-border);
            backdrop-filter: blur(10px);
            opacity: 0.3;
            transition: opacity 0.3s ease;
        }
        
        .nav-controls:hover {
                opacity: 1;
        }
        
        .nav-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: transparent;
            border: 2px solid var(--neon-cyan);
            color: var(--neon-cyan);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 1.2rem;
        }
        
        .nav-btn:hover {
            background: var(--neon-cyan);
            color: var(--dark-bg);
            box-shadow: 0 0 20px rgba(0, 255, 247, 0.5);
        }
        
        .nav-btn:disabled {
            opacity: 0.2;
            cursor: not-allowed;
        }
        
        .nav-btn:disabled:hover {
            background: transparent;
            color: var(--neon-cyan);
            box-shadow: none;
        }
        
        .slide-indicator {
            display: flex;
            gap: 6px;
        }
        
        .indicator-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--dark-card-border);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .indicator-dot:hover {
            background: var(--text-secondary);
        }
        
        .indicator-dot.active {
            background: var(--neon-cyan);
            box-shadow: 0 0 10px rgba(0, 255, 247, 0.5);
            transform: scale(1.2);
        }
        
        /* Footer */
        .slide-footer {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-align: center;
            margin-top: 40px;
        }
        
        /* Share button */
        .share-btn {
            margin-top: 30px;
            padding: 15px 40px;
            font-size: 1rem;
            font-weight: 600;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
            border: none;
            border-radius: 50px;
            color: var(--dark-bg);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-family: 'Orbitron', monospace;
        }
        
        .share-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: btnShine 3s infinite;
        }
        
        .share-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(0, 255, 247, 0.5);
        }
        
        .share-btn:active {
            transform: scale(0.98);
        }
        
        .share-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Final slide */
        .final-slide h2 {
            font-family: 'Orbitron', monospace;
            font-size: clamp(2rem, 6vw, 4rem);
            font-weight: 700;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
        }
        
        .final-slide .tagline {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 40px;
        }
        
        .stats-summary {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        
        .stat-item {
            text-align: center;
            padding: 15px;
        }
        
        .stat-value {
            font-family: 'Orbitron', monospace;
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--neon-cyan);
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 5px;
        }
        
        /* Radial Hour Chart */
        .radial-chart-container {
            width: 350px;
            height: 350px;
            margin: 30px auto;
            position: relative;
        }
        
        .radial-chart-container svg {
            width: 100%;
            height: 100%;
        }
        
        .radial-bar {
            transition: all 0.3s ease;
        }
        
        .radial-bar:hover {
            filter: brightness(1.3);
        }
        
        .radial-label {
            font-size: 10px;
            fill: var(--text-secondary);
        }
        
        .radial-center-text {
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            fill: var(--neon-cyan);
        }
        
        /* Time Pattern Cards */
        .time-patterns {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 30px;
        }
        
        .time-card {
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.9), rgba(30, 30, 46, 0.7));
            border: 1px solid var(--dark-card-border);
            border-radius: 15px;
            padding: 20px 30px;
            text-align: center;
            min-width: 140px;
        }
        
        .time-card.highlight {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 20px rgba(0, 255, 247, 0.2);
        }
        
        .time-value {
            font-family: 'Orbitron', monospace;
            font-size: 2rem;
            font-weight: 700;
            color: var(--neon-cyan);
        }
        
        .time-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 5px;
        }
        
        /* Badges */
        .badges-container {
            display: flex;
            gap: 25px;
            margin: 30px auto;
            overflow-x: auto;
            overflow-y: hidden;
            padding: 20px 50%;
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: var(--neon-cyan) rgba(18, 18, 26, 0.5);
            width: 100%;
            max-width: 100%;
            position: relative;
        }
        
        .badges-container::-webkit-scrollbar {
            height: 8px;
        }
        
        .badges-container::-webkit-scrollbar-track {
            background: rgba(18, 18, 26, 0.5);
            border-radius: 10px;
        }
        
        .badges-container::-webkit-scrollbar-thumb {
            background: var(--neon-cyan);
            border-radius: 10px;
        }
        
        .badges-container::-webkit-scrollbar-thumb:hover {
            background: var(--neon-magenta);
        }
        
        .badge {
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.95), rgba(30, 30, 46, 0.8));
            border: 2px solid var(--dark-card-border);
            border-radius: 20px;
            padding: 25px 30px;
            text-align: center;
            min-width: 200px;
            max-width: 220px;
            flex-shrink: 0;
            transition: all 0.3s ease;
        }
        
        .badge.earned {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 25px rgba(0, 255, 247, 0.3);
        }
        
        .badge.special {
            border-color: var(--neon-magenta);
            box-shadow: 0 0 25px rgba(255, 0, 255, 0.3);
        }
        
        .badge-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .badge-title {
            font-family: 'Orbitron', monospace;
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .badge-description {
            font-size: 0.75rem;
            color: var(--text-secondary);
            line-height: 1.4;
        }
        
        .badge-value {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            color: var(--neon-cyan);
            margin-top: 10px;
        }
        
        /* Download Growth Chart */
        .growth-chart-container {
            width: 100%;
            max-width: 800px;
            height: 300px;
            margin: 30px auto;
            background: rgba(18, 18, 26, 0.8);
            border-radius: 20px;
            border: 1px solid var(--dark-card-border);
            padding: 20px;
        }
        
        .growth-chart-container svg {
            width: 100%;
            height: 100%;
        }
        
        .chart-line {
            fill: none;
            stroke: var(--neon-cyan);
            stroke-width: 3;
        }
        
        .chart-area {
            fill: url(#chartGradient);
        }
        
        .chart-dot {
            fill: var(--neon-cyan);
            stroke: var(--dark-bg);
            stroke-width: 2;
        }
        
        .chart-axis text {
            fill: var(--text-secondary);
            font-size: 11px;
        }
        
        .chart-axis line, .chart-axis path {
            stroke: var(--dark-card-border);
        }
        
        .chart-grid line {
            stroke: var(--dark-card-border);
            stroke-opacity: 0.3;
        }
        
        /* First Download Card */
        .first-download-card {
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.9), rgba(30, 30, 46, 0.7));
            border: 1px solid var(--neon-cyan);
            border-radius: 20px;
            padding: 30px 40px;
            max-width: 500px;
            margin: 30px auto;
            text-align: left;
            box-shadow: 0 0 30px rgba(0, 255, 247, 0.2);
        }
        
        .first-download-date {
            font-family: 'Orbitron', monospace;
            font-size: 1.8rem;
            color: var(--neon-cyan);
            margin-bottom: 15px;
        }
        
        .first-download-file {
            font-size: 1rem;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .first-download-project {
            font-size: 0.85rem;
            color: var(--neon-purple);
        }
        
        /* Busiest Day Card */
        .busiest-day-card {
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(255, 0, 255, 0.1));
            border: 1px solid var(--neon-magenta);
            border-radius: 20px;
            padding: 30px 40px;
            max-width: 500px;
            margin: 30px auto;
            text-align: center;
            box-shadow: 0 0 30px rgba(255, 0, 255, 0.2);
        }
        
        .busiest-day-date {
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            color: var(--neon-magenta);
            margin-bottom: 15px;
        }
        
        .busiest-day-stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .busiest-stat {
            text-align: center;
        }
        
        .busiest-stat-value {
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            color: var(--text-primary);
        }
        
        .busiest-stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        /* Largest File Card */
        .largest-file-card {
            background: linear-gradient(135deg, rgba(18, 18, 26, 0.9), rgba(30, 30, 46, 0.7));
            border: 1px solid var(--neon-purple);
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            margin: 20px auto;
            text-align: center;
        }
        
        .largest-file-size {
            font-family: 'Orbitron', monospace;
            font-size: 2.5rem;
            color: var(--neon-purple);
            margin-bottom: 10px;
        }
        
        .largest-file-name {
            font-size: 1rem;
            color: var(--text-primary);
            margin-bottom: 5px;
            word-break: break-all;
        }
        
        .largest-file-project {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        /* Comparison bar */
        .comparison-bar {
            margin: 30px auto;
            max-width: 400px;
        }
        
        .comparison-labels {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .comparison-track {
            height: 12px;
            background: var(--dark-card);
            border-radius: 6px;
            position: relative;
            overflow: hidden;
        }
        
        .comparison-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
            border-radius: 6px;
            transition: width 1s ease;
        }
        
        .comparison-marker {
            position: absolute;
            top: -5px;
            width: 4px;
            height: 22px;
            background: var(--neon-magenta);
            border-radius: 2px;
            transform: translateX(-50%);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .slide {
                padding: 20px;
                padding-bottom: 100px;
            }
            
            .nav-controls {
                bottom: 15px;
                padding: 10px 15px;
            }
            
            .project-item, .collaborator-item {
                padding: 12px 15px;
            }
            
            .creation-breakdown {
                gap: 15px;
            }
            
            .creation-item {
                padding: 15px 20px;
                min-width: 100px;
            }
            
            #network-container {
                height: 350px;
            }
            
            .heatmap-cell {
                width: 8px;
                height: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="particles" id="particles"></div>
    <div class="grid-overlay"></div>
    
    <div class="slides-container">
        <!-- Slide 0: Title -->
        <div class="slide active title-slide" data-slide="0">
            <div class="slide-content">
                <div class="logo animate-in">SYNAPSE</div>
                <h1 class="animate-in">WRAPPED</h1>
                <div class="year animate-in">{year}</div>
                <div class="username animate-in">{username}</div>
                <button class="start-btn animate-in" onclick="nextSlide()">BEGIN YOUR JOURNEY</button>
        </div>
        </div>
        
        <!-- Slide 1: Your Synapse Year Started -->
        <div class="slide" data-slide="1">
            <div class="slide-content">
                <div class="metric-label animate-in">Your {year} Synapse Journey Began On...</div>
                <div class="first-download-card animate-in">
                    <div class="first-download-date">{first_download_date}</div>
                    <div class="first-download-file">📁 {first_download_file}</div>
                    <div class="first-download-project">from {first_download_project}</div>
                </div>
                <div class="busiest-day-card animate-in">
                    <div class="metric-label" style="margin-bottom: 10px;">Your Busiest Day</div>
                    <div class="busiest-day-date">{busiest_day_date}</div>
                    <div class="busiest-day-stats">
                        <div class="busiest-stat">
                            <div class="busiest-stat-value">{busiest_day_downloads}</div>
                            <div class="busiest-stat-label">downloads</div>
                        </div>
                        <div class="busiest-stat">
                            <div class="busiest-stat-value">{busiest_day_size}</div>
                            <div class="busiest-stat-label">data</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Slide 2: Days Active -->
        <div class="slide" data-slide="2">
            <div class="slide-content">
                <div class="metric-label animate-in">You were active on Synapse for</div>
                <div class="metric-value animate-in">{active_days}</div>
                <div class="metric-unit animate-in">days</div>
                <div class="metric-context animate-in">That's {active_percentage}% of {year}. Your dedication to science is inspiring.</div>
            </div>
        </div>
        
        <!-- Slide 3: Files Downloaded -->
        <div class="slide" data-slide="3">
            <div class="slide-content">
                <div class="metric-label animate-in">This year, you downloaded</div>
                <div class="metric-value animate-in">{file_count}</div>
                <div class="metric-unit animate-in">files</div>
                <div class="metric-context animate-in">That's {total_size} of scientific data flowing through your research pipeline.</div>
            </div>
        </div>
        
        <!-- Slide 4: Activity Heatmap -->
        <div class="slide" data-slide="4">
            <div class="slide-content">
                <div class="metric-label animate-in">Your Activity Throughout {year}</div>
                {heatmap_html}
                <div class="active-months animate-in">
                    {most_active_months_html}
                </div>
            </div>
        </div>
        
        <!-- Slide 5: Activity by Hour -->
        <div class="slide" data-slide="5">
            <div class="slide-content">
                <div class="metric-label animate-in">When Do You Download?</div>
                <div class="metric-context animate-in" style="margin-bottom: 10px;">Times shown in {timezone_display}</div>
                <div class="radial-chart-container animate-in" id="radial-chart"></div>
                <div class="time-patterns animate-in">
                    <div class="time-card {night_owl_class}">
                        <div class="time-value">{night_owl_score}%</div>
                        <div class="time-label">🌙 Night Owl</div>
                    </div>
                    <div class="time-card {early_bird_class}">
                        <div class="time-value">{early_bird_score}%</div>
                        <div class="time-label">🌅 Early Bird</div>
                    </div>
                    <div class="time-card {weekend_class}">
                        <div class="time-value">{weekend_score}%</div>
                        <div class="time-label">📅 Weekend</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Slide 6: Projects Explored -->
        <div class="slide slide-wordcloud" data-slide="6">
            <div class="slide-content">
                <div class="metric-label animate-in">You explored data from</div>
                <div class="metric-value animate-in">{project_count}</div>
                <div class="metric-unit animate-in">unique projects</div>
                {wordcloud_html}
            </div>
        </div>
        
        <!-- Slide 7: Top Projects Downloaded From -->
        <div class="slide" data-slide="7">
            <div class="slide-content">
                <div class="metric-label animate-in">Your Top Projects (by downloads)</div>
                {top_projects_html}
            </div>
        </div>
        
        <!-- Slide 8: Content Created -->
        <div class="slide" data-slide="8">
            <div class="slide-content">
                <div class="metric-label animate-in">You created</div>
                <div class="metric-value animate-in">{total_creations}</div>
                <div class="metric-unit animate-in">items on Synapse</div>
                <div class="creation-breakdown">
                    <div class="creation-item">
                        <div class="creation-count">{projects_created}</div>
                        <div class="creation-type">Projects</div>
                    </div>
                    <div class="creation-item">
                        <div class="creation-count">{files_created}</div>
                        <div class="creation-type">Files</div>
                    </div>
                    <div class="creation-item">
                        <div class="creation-count">{tables_created}</div>
                        <div class="creation-type">Tables</div>
                    </div>
                    <div class="creation-item">
                        <div class="creation-count">{folders_created}</div>
                        <div class="creation-type">Folders</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Slide 9: Users Like You -->
        <div class="slide" data-slide="9">
            <div class="slide-content">
                <div class="metric-label animate-in">Users Like You</div>
                <div class="metric-context animate-in" style="margin-bottom: 20px;">Researchers with similar download patterns</div>
                {top_collaborators_html}
            </div>
        </div>
        
        <!-- Slide 10: Collaboration Network -->
        <div class="slide" data-slide="10">
            <div class="slide-content">
                <div class="metric-label animate-in">Your Research Network</div>
                <div class="metric-context animate-in" style="margin-top: 10px; margin-bottom: 10px;">Users who downloaded the same files as you</div>
                <div id="network-container" class="animate-in"></div>
            </div>
        </div>
        
        <!-- Slide 11: Data Size Stats -->
        <div class="slide" data-slide="11">
            <div class="slide-content">
                <div class="metric-label animate-in">Your Biggest Download</div>
                <div class="largest-file-card animate-in">
                    <div class="largest-file-size">{largest_file_size}</div>
                    <div class="largest-file-name">{largest_file_name}</div>
                    <div class="largest-file-project">{largest_file_project}</div>
                </div>
                <div class="metric-label animate-in" style="margin-top: 30px;">Your Average File Size vs Platform</div>
                <div class="comparison-bar animate-in">
                    <div class="comparison-labels">
                        <span>Platform avg: {platform_avg_size}</span>
                        <span>You: {user_avg_size}</span>
                    </div>
                    <div class="comparison-track">
                        <div class="comparison-fill" style="width: {comparison_percent}%;"></div>
                    </div>
                </div>
                <div class="metric-context animate-in">{size_comparison_text}</div>
            </div>
        </div>
        
        <!-- Slide 12: Download Growth -->
        <div class="slide" data-slide="12">
            <div class="slide-content">
                <div class="metric-label animate-in">Your Download Journey</div>
                <div class="metric-context animate-in">Cumulative data downloaded throughout {year}</div>
                <div class="growth-chart-container animate-in" id="growth-chart"></div>
            </div>
        </div>
        
        <!-- Slide 13: Your Badges -->
        <div class="slide" data-slide="13">
            <div class="slide-content">
                <div class="metric-label animate-in">Your Badges</div>
                <div class="badges-container animate-in">
                    {badges_html}
                </div>
            </div>
        </div>
        
        <!-- Slide 14: Summary -->
        <div class="slide final-slide" data-slide="14">
            <div class="slide-content">
                <h2 class="animate-in">That's a Wrap!</h2>
                <div class="tagline animate-in">Here's to another year of groundbreaking research</div>
                <div class="stats-summary">
                    <div class="stat-item animate-in">
                        <div class="stat-value">{file_count}</div>
                        <div class="stat-label">Files Downloaded</div>
                    </div>
                    <div class="stat-item animate-in">
                        <div class="stat-value">{active_days}</div>
                        <div class="stat-label">Active Days</div>
                    </div>
                    <div class="stat-item animate-in">
                        <div class="stat-value">{project_count}</div>
                        <div class="stat-label">Projects Explored</div>
                    </div>
                    <div class="stat-item animate-in">
                        <div class="stat-value">{total_creations}</div>
                        <div class="stat-label">Items Created</div>
                    </div>
                </div>
                <button class="share-btn animate-in" onclick="shareWrapped()" id="share-btn">
                    ✨ Share Your Synapse Wrapped
                </button>
                <div class="slide-footer animate-in">
            <p>Generated on {generation_date}</p>
            <p>Powered by Synapse Data Warehouse</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="nav-controls">
        <button class="nav-btn" id="prev-btn" onclick="prevSlide()" disabled>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="15,18 9,12 15,6"></polyline>
            </svg>
        </button>
        <div class="slide-indicator" id="indicators"></div>
        <button class="nav-btn" id="next-btn" onclick="nextSlide()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9,18 15,12 9,6"></polyline>
            </svg>
        </button>
    </div>
    
    <script>
        // Generate floating particles
        const particlesContainer = document.getElementById('particles');
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.width = (Math.random() * 4 + 2) + 'px';
            particle.style.height = particle.style.width;
            particlesContainer.appendChild(particle);
        }
        
        let currentSlide = 0;
        const totalSlides = document.querySelectorAll('.slide').length;
        
        // Create indicators
        const indicatorsContainer = document.getElementById('indicators');
        for (let i = 0; i < totalSlides; i++) {
            const dot = document.createElement('div');
            dot.className = 'indicator-dot' + (i === 0 ? ' active' : '');
            dot.onclick = () => goToSlide(i);
            indicatorsContainer.appendChild(dot);
        }
        
        function updateSlide() {
            const slides = document.querySelectorAll('.slide');
            const dots = document.querySelectorAll('.indicator-dot');
            const prevBtn = document.getElementById('prev-btn');
            const nextBtn = document.getElementById('next-btn');
            
            slides.forEach((slide, index) => {
                slide.classList.remove('active', 'prev', 'next');
                // Reset animations
                slide.querySelectorAll('.animate-in').forEach(el => {
                    el.style.animation = 'none';
                    el.offsetHeight; // Trigger reflow
                    el.style.animation = null;
                });
                
                if (index === currentSlide) {
                    slide.classList.add('active');
                    // Initialize visualizations on specific slides
                    if (index === 10) {
                        setTimeout(initNetwork, 300);
                    }
                    if (index === 5) {
                        setTimeout(initRadialChart, 300);
                    }
                    if (index === 12) {
                        setTimeout(initGrowthChart, 300);
                    }
                    if (index === 13) {
                        setTimeout(initBadgeCarousel, 300);
                    }
                } else if (index < currentSlide) {
                    slide.classList.add('prev');
                } else {
                    slide.classList.add('next');
                }
            });
            
            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === currentSlide);
            });
            
            prevBtn.disabled = currentSlide === 0;
            nextBtn.disabled = currentSlide === totalSlides - 1;
        }
        
        function nextSlide() {
            if (currentSlide < totalSlides - 1) {
                currentSlide++;
                updateSlide();
            }
        }
        
        function prevSlide() {
            if (currentSlide > 0) {
                currentSlide--;
                updateSlide();
            }
        }
        
        function goToSlide(index) {
            currentSlide = index;
            updateSlide();
        }
        
        // Share functionality - draw static image with Canvas API
        function shareWrapped() {
            const shareBtn = document.getElementById('share-btn');
            
            try {
                // Disable button and show loading state
                shareBtn.disabled = true;
                shareBtn.textContent = '📸 Creating image...';
                
                // Create canvas
                const canvas = document.createElement('canvas');
                canvas.width = 1920;
                canvas.height = 1080;
                const ctx = canvas.getContext('2d');
                
                // Draw background gradient (matching the slide)
                const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
                gradient.addColorStop(0, '#0a0a0f');
                gradient.addColorStop(0.5, '#1a0a1f');
                gradient.addColorStop(1, '#0a0a0f');
                ctx.fillStyle = gradient;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Add decorative glowing circles
                ctx.fillStyle = 'rgba(0, 255, 247, 0.03)';
                for (let i = 0; i < 15; i++) {
                    const x = Math.random() * canvas.width;
                    const y = Math.random() * canvas.height;
                    const size = Math.random() * 150 + 100;
                    ctx.beginPath();
                    ctx.arc(x, y, size, 0, Math.PI * 2);
                    ctx.fill();
                }
                
                // Add magenta/purple accents
                ctx.fillStyle = 'rgba(255, 0, 255, 0.02)';
                for (let i = 0; i < 10; i++) {
                    const x = Math.random() * canvas.width;
                    const y = Math.random() * canvas.height;
                    const size = Math.random() * 120 + 80;
                    ctx.beginPath();
                    ctx.arc(x, y, size, 0, Math.PI * 2);
                    ctx.fill();
                }
                
                // Title with gradient effect (simulated with cyan) - matching h2 on final slide
                ctx.fillStyle = '#00fff7';
                ctx.font = 'bold 96px Orbitron, monospace';
                ctx.textAlign = 'center';
                ctx.fillText("That's a Wrap! 🎉", canvas.width / 2, 180);
                
                // Tagline - matching final slide tagline
                ctx.fillStyle = '#a0a0b0';
                ctx.font = '36px "Exo 2", sans-serif';
                ctx.fillText("Here's to another year of groundbreaking research 🔬", canvas.width / 2, 250);
                
                // Stats data with emojis
                const stats = [
                    { emoji: '📥', value: '{file_count}', label: 'Files Downloaded' },
                    { emoji: '📅', value: '{active_days}', label: 'Active Days' },
                    { emoji: '🔭', value: '{project_count}', label: 'Projects Explored' },
                    { emoji: '✨', value: '{total_creations}', label: 'Items Created' }
                ];
                
                // Draw stats in horizontal layout like the slide
                const startY = 400;
                const statWidth = 380;
                const spacing = 40;
                const totalWidth = stats.length * statWidth + (stats.length - 1) * spacing;
                const startX = (canvas.width - totalWidth) / 2;
                
                stats.forEach((stat, index) => {
                    const x = startX + index * (statWidth + spacing);
                    const y = startY;
                    
                    // Draw subtle background box
                    ctx.fillStyle = 'rgba(18, 18, 26, 0.5)';
                    ctx.fillRect(x, y, statWidth, 240);
                    
                    // Draw border with gradient effect (cyan glow)
                    ctx.strokeStyle = 'rgba(0, 255, 247, 0.3)';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x, y, statWidth, 240);
                    
                    // Draw emoji at the top
                    ctx.font = '48px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(stat.emoji, x + statWidth / 2, y + 70);
                    
                    // Draw value (number) - matching .stat-value (Orbitron monospace)
                    ctx.fillStyle = '#00fff7';
                    ctx.font = 'bold 64px Orbitron, monospace';
                    ctx.fillText(stat.value, x + statWidth / 2, y + 150);
                    
                    // Draw label - matching .stat-label (Exo 2, uppercase)
                    ctx.fillStyle = '#a0a0b0';
                    ctx.font = '18px "Exo 2", sans-serif';
                    ctx.fillText(stat.label.toUpperCase(), x + statWidth / 2, y + 195);
                });
                
                // Footer - matching slide footer style
                ctx.fillStyle = '#a0a0b0';
                ctx.font = '28px "Exo 2", sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('SYNAPSE WRAPPED {year} 🧬', canvas.width / 2, 900);
                
                ctx.font = '24px "Exo 2", sans-serif';
                ctx.fillStyle = '#00fff7';
                ctx.fillText('{username}', canvas.width / 2, 960);
                
                ctx.fillStyle = '#6b7280';
                ctx.font = '20px "Exo 2", sans-serif';
                ctx.fillText('Generated on {generation_date} • Powered by Synapse Data Warehouse', canvas.width / 2, 1020);
                
                // Convert to blob and download
                canvas.toBlob((blob) => {
                    if (blob) {
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        const year = '{year}';
                        const username = '{username}'.replace('@', '_at_').replace(/[^a-zA-Z0-9_]/g, '_');
                        link.download = `synapse_wrapped_${year}_${username}.png`;
                        link.href = url;
                        link.click();
                        URL.revokeObjectURL(url);
                    }
                    
                    // Restore button
                    shareBtn.disabled = false;
                    shareBtn.textContent = '✨ Share Your Synapse Wrapped';
                }, 'image/png', 1.0);
                
            } catch (error) {
                console.error('Error creating image:', error);
                shareBtn.disabled = false;
                shareBtn.textContent = '✨ Share Your Synapse Wrapped';
                alert('Unable to create image. Error: ' + error.message);
            }
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                e.preventDefault();
                nextSlide();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                prevSlide();
            }
        });
        
        // Touch/swipe support
        let touchStartX = 0;
        let touchEndX = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });
        
        function handleSwipe() {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;
            
            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    nextSlide();
                } else {
                    prevSlide();
                }
            }
        }
        
        // Network visualization data
        const networkData = {network_data_json};
        
        // Hourly activity data for radial chart
        const hourlyData = {hourly_data_json};
        
        // Monthly download data for growth chart
        const monthlyGrowthData = {monthly_growth_json};
        
        let networkInitialized = false;
        let radialChartInitialized = false;
        let growthChartInitialized = false;
        
        function initRadialChart() {
            if (radialChartInitialized || !hourlyData || hourlyData.length === 0) return;
            radialChartInitialized = true;
            
            const container = document.getElementById('radial-chart');
            if (!container) return;
            
            const width = 350;
            const height = 350;
            const innerRadius = 60;
            const outerRadius = Math.min(width, height) / 2 - 30;
            
            const svg = d3.select('#radial-chart')
                .append('svg')
                .attr('viewBox', `0 0 ${width} ${height}`)
                .append('g')
                .attr('transform', `translate(${width/2}, ${height/2})`);
            
            // Fill in missing hours with 0
            const fullData = [];
            for (let h = 0; h < 24; h++) {
                const found = hourlyData.find(d => d.hour === h);
                fullData.push({ hour: h, count: found ? found.count : 0 });
            }
            
            const maxCount = d3.max(fullData, d => d.count) || 1;
            
            const angleScale = d3.scaleLinear()
                .domain([0, 24])
                .range([0, 2 * Math.PI]);
            
            const radiusScale = d3.scaleLinear()
                .domain([0, maxCount])
                .range([innerRadius, outerRadius]);
            
            // Draw bars
            const arc = d3.arc()
                .innerRadius(innerRadius)
                .outerRadius(d => radiusScale(d.count))
                .startAngle(d => angleScale(d.hour) - Math.PI / 24)
                .endAngle(d => angleScale(d.hour) + Math.PI / 24)
                .padAngle(0.02)
                .cornerRadius(3);
            
            svg.selectAll('.radial-bar')
                .data(fullData)
                .join('path')
                .attr('class', 'radial-bar')
                .attr('d', arc)
                .attr('fill', d => {
                    if (d.hour >= 18 || d.hour < 6) return '#a855f7';
                    if (d.hour >= 5 && d.hour < 9) return '#ff6b9d';
                    return '#00fff7';
                })
                .attr('opacity', d => 0.4 + 0.6 * (d.count / maxCount))
                .append('title')
                .text(d => `${d.hour}:00 - ${d.count} downloads`);
            
            // Hour labels
            const hours = [0, 6, 12, 18];
            const labels = ['12am', '6am', '12pm', '6pm'];
            
            svg.selectAll('.radial-label')
                .data(hours)
                .join('text')
                .attr('class', 'radial-label')
                .attr('x', (d, i) => (outerRadius + 15) * Math.sin(angleScale(d)))
                .attr('y', (d, i) => -(outerRadius + 15) * Math.cos(angleScale(d)))
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .text((d, i) => labels[i]);
            
            // Center text
            const peakHour = fullData.reduce((a, b) => a.count > b.count ? a : b);
            svg.append('text')
                .attr('class', 'radial-center-text')
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('y', -5)
                .text(`${peakHour.hour}:00`);
            
            svg.append('text')
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('y', 15)
                .attr('fill', '#a0a0b0')
                .attr('font-size', '12px')
                .text('peak hour');
        }
        
        function initGrowthChart() {
            if (growthChartInitialized || !monthlyGrowthData || monthlyGrowthData.length === 0) return;
            growthChartInitialized = true;
            
            const container = document.getElementById('growth-chart');
            if (!container) return;
            
            const margin = { top: 20, right: 30, bottom: 40, left: 60 };
            const width = container.clientWidth - margin.left - margin.right;
            const height = 260 - margin.top - margin.bottom;
            
            const svg = d3.select('#growth-chart')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${margin.left}, ${margin.top})`);
            
            // Create gradient
            const defs = svg.append('defs');
            const gradient = defs.append('linearGradient')
                .attr('id', 'chartGradient')
                .attr('x1', '0%').attr('y1', '0%')
                .attr('x2', '0%').attr('y2', '100%');
            gradient.append('stop').attr('offset', '0%').attr('stop-color', '#00fff7').attr('stop-opacity', 0.4);
            gradient.append('stop').attr('offset', '100%').attr('stop-color', '#00fff7').attr('stop-opacity', 0.05);
            
            // Calculate cumulative data
            let cumulative = 0;
            const cumulativeData = monthlyGrowthData.map(d => {
                cumulative += d.size;
                return { month: new Date(d.month), size: d.size, cumulative: cumulative };
            });
            
            // Scales
            const x = d3.scaleTime()
                .domain(d3.extent(cumulativeData, d => d.month))
                .range([0, width]);
            
            const y = d3.scaleLinear()
                .domain([0, d3.max(cumulativeData, d => d.cumulative)])
                .nice()
                .range([height, 0]);
            
            // Format bytes
            const formatBytes = (bytes) => {
                if (bytes >= 1e12) return (bytes / 1e12).toFixed(1) + ' TB';
                if (bytes >= 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
                if (bytes >= 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
                return (bytes / 1e3).toFixed(1) + ' KB';
            };
            
            // Grid
            svg.append('g')
                .attr('class', 'chart-grid')
                .selectAll('line')
                .data(y.ticks(5))
                .join('line')
                .attr('x1', 0).attr('x2', width)
                .attr('y1', d => y(d)).attr('y2', d => y(d));
            
            // Area
            const area = d3.area()
                .x(d => x(d.month))
                .y0(height)
                .y1(d => y(d.cumulative))
                .curve(d3.curveMonotoneX);
            
            svg.append('path')
                .datum(cumulativeData)
                .attr('class', 'chart-area')
                .attr('d', area);
            
            // Line
            const line = d3.line()
                .x(d => x(d.month))
                .y(d => y(d.cumulative))
                .curve(d3.curveMonotoneX);
            
            svg.append('path')
                .datum(cumulativeData)
                .attr('class', 'chart-line')
                .attr('d', line);
            
            // Dots
            svg.selectAll('.chart-dot')
                .data(cumulativeData)
                .join('circle')
                .attr('class', 'chart-dot')
                .attr('cx', d => x(d.month))
                .attr('cy', d => y(d.cumulative))
                .attr('r', 5)
                .append('title')
                .text(d => `${d.month.toLocaleDateString('en-US', { month: 'short' })}: ${formatBytes(d.cumulative)}`);
            
            // Axes
            svg.append('g')
                .attr('class', 'chart-axis')
                .attr('transform', `translate(0, ${height})`)
                .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b')));
            
            svg.append('g')
                .attr('class', 'chart-axis')
                .call(d3.axisLeft(y).ticks(5).tickFormat(formatBytes));
        }
        
        let badgeCarouselInitialized = false;
        let badgeCarouselInterval = null;
        
        function initBadgeCarousel() {
            if (badgeCarouselInitialized) return;
            badgeCarouselInitialized = true;
            
            const container = document.querySelector('.badges-container');
            if (!container) return;
            
            const badges = container.querySelectorAll('.badge');
            if (badges.length === 0) return;
            
            // Center the first badge initially
            const firstBadge = badges[0];
            const badgeWidth = firstBadge.offsetWidth + 25; // width + gap
            const containerWidth = container.offsetWidth;
            const scrollPosition = (firstBadge.offsetLeft - containerWidth / 2) + (badgeWidth / 2);
            container.scrollLeft = scrollPosition;
            
            let currentIndex = 0;
            const totalBadges = badges.length;
            
            // Auto-rotate carousel
            function rotateCarousel() {
                currentIndex = (currentIndex + 1) % totalBadges;
                const targetBadge = badges[currentIndex];
                const badgeWidth = targetBadge.offsetWidth + 25;
                const containerWidth = container.offsetWidth;
                const scrollPosition = (targetBadge.offsetLeft - containerWidth / 2) + (badgeWidth / 2);
                
                container.scrollTo({
                    left: scrollPosition,
                    behavior: 'smooth'
                });
            }
            
            // Start auto-rotation (every 3 seconds)
            badgeCarouselInterval = setInterval(rotateCarousel, 3000);
            
            // Pause on hover
            container.addEventListener('mouseenter', () => {
                if (badgeCarouselInterval) {
                    clearInterval(badgeCarouselInterval);
                    badgeCarouselInterval = null;
                }
            });
            
            // Resume on mouse leave
            container.addEventListener('mouseleave', () => {
                if (!badgeCarouselInterval) {
                    badgeCarouselInterval = setInterval(rotateCarousel, 3000);
                }
            });
            
            // Pause on manual scroll
            let scrollTimeout;
            container.addEventListener('scroll', () => {
                if (badgeCarouselInterval) {
                    clearInterval(badgeCarouselInterval);
                    badgeCarouselInterval = null;
                }
                
                // Resume after 5 seconds of no scrolling
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    if (!badgeCarouselInterval) {
                        badgeCarouselInterval = setInterval(rotateCarousel, 3000);
                    }
                }, 5000);
            });
        }
        
        function initNetwork() {
            if (networkInitialized || !networkData || networkData.nodes.length === 0) return;
            networkInitialized = true;
            
            const container = document.getElementById('network-container');
            if (!container) return;
            
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            // Clear any existing content
            container.innerHTML = '';
            
            // Create SVG
            const svg = d3.select('#network-container')
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            // Create tooltip
            const tooltip = d3.select('body')
                .append('div')
                .attr('class', 'network-tooltip')
                .style('opacity', 0);
            
            // Calculate edge weight scale
            const maxWeight = d3.max(networkData.links, d => d.weight) || 1;
            const minWeight = d3.min(networkData.links, d => d.weight) || 1;
            const weightScale = d3.scaleLinear()
                .domain([minWeight, maxWeight])
                .range([1, 8]);
            
            // Create simulation - run it "hot" first to settle positions
            const simulation = d3.forceSimulation(networkData.nodes)
                .force('link', d3.forceLink(networkData.links).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(40))
                .alphaDecay(0.05);  // Settle faster
            
            // Pre-run simulation to settle initial positions (no animation lag)
            for (let i = 0; i < 100; i++) {
                simulation.tick();
            }
            
            // Clamp all node positions after settling
            networkData.nodes.forEach(d => {
                d.x = Math.max(30, Math.min(width - 30, d.x));
                d.y = Math.max(30, Math.min(height - 30, d.y));
            });
            
            // Create links
            const link = svg.append('g')
                .selectAll('line')
                .data(networkData.links)
                .join('line')
                .attr('class', 'network-link')
                .attr('stroke', '#00fff7')
                .attr('stroke-width', d => weightScale(d.weight))
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            // Create nodes
            const node = svg.append('g')
                .selectAll('circle')
                .data(networkData.nodes)
                .join('circle')
                .attr('class', 'network-node')
                .attr('r', d => d.isCenter ? 25 : 15)
                .attr('fill', d => d.isCenter ? '#00fff7' : '#a855f7')
                .attr('cx', d => d.x)
                .attr('cy', d => d.y)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('mouseover', function(event, d) {
                    tooltip.transition().duration(200).style('opacity', 1);
                    tooltip.html('<strong>' + d.name + '</strong><br/>Shared files: ' + (d.sharedFiles || 'N/A'))
                        .style('left', (event.pageX + 10) + 'px')
                        .style('top', (event.pageY - 10) + 'px');
                })
                .on('mouseout', function() {
                    tooltip.transition().duration(500).style('opacity', 0);
                })
                .on('click', function(event, d) {
                    if (d.profileUrl) {
                        window.open(d.profileUrl, '_blank');
                    }
                });
            
            // Create labels for important nodes
            const label = svg.append('g')
                .selectAll('text')
                .data(networkData.nodes.filter(d => d.isCenter || d.showLabel))
                .join('text')
                .attr('class', 'network-label')
                .attr('text-anchor', 'middle')
                .attr('dy', d => d.isCenter ? 40 : 30)
                .attr('x', d => d.x)
                .attr('y', d => d.y)
                .text(d => d.name);
            
            // Stop simulation initially (graph is already settled)
            simulation.stop();
            
            // Only animate on drag interactions
            simulation.on('tick', () => {
                // Update node positions first (with clamping)
                node
                    .attr('cx', d => {
                        d.x = Math.max(30, Math.min(width - 30, d.x));
                        return d.x;
                    })
                    .attr('cy', d => {
                        d.y = Math.max(30, Math.min(height - 30, d.y));
                        return d.y;
                    });
                
                // Then update links using clamped positions
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });
            
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
        }
    </script>
</body>
</html>
"""


def generate_top_projects_html(top_projects_df: pd.DataFrame) -> str:
    """Generate HTML for top projects list in the new template style."""
    if top_projects_df.empty:
        return '<p style="color: var(--text-secondary);">No project data available</p>'
    
    html = '<div class="project-list">'
    rank = 0
    for idx, row in top_projects_df.iterrows():
        project_name = row.get('project_name', None)
        project_id = row.get('project_id', None)
        
        # Handle None/null/nan project names and IDs - skip unnamed projects (likely deleted)
        has_valid_name = project_name is not None and not pd.isna(project_name) and str(project_name).strip().lower() not in ('none', 'null', 'nan', '')
        has_valid_id = project_id is not None and not pd.isna(project_id)
        
        if not has_valid_name and not has_valid_id:
            continue  # Skip this entry entirely
        
        if not has_valid_name:
            project_name = f"syn{int(project_id)}"
        
        file_count = row.get('file_count', 0)
        rank += 1
        
        # Create link to project if we have an ID
        project_link = f"https://www.synapse.org/#!Synapse:syn{int(project_id)}" if has_valid_id else "#"
        
        html += f"""
        <div class="project-item" onclick="window.open('{project_link}', '_blank')" style="cursor: pointer;">
            <div class="project-rank">{rank}</div>
            <div class="project-info">
                <div class="project-name">{project_name}</div>
                <div class="project-metric">{file_count:,} files downloaded</div>
            </div>
        </div>
        """
    html += '</div>'
    return html


def generate_top_collaborators_html(collaborators_df: pd.DataFrame) -> str:
    """Generate HTML for users like you list in the new template style."""
    if collaborators_df.empty:
        return '<p style="color: var(--text-secondary);">No similar users found</p>'
    
    html = '<div class="collaborator-list">'
    rank = 0
    for idx, row in collaborators_df.iterrows():
        user_id = row.get('user_id', None)
        collab_name = row.get('collaborator_name', f"User {user_id}" if user_id else "Unknown")
        shared_projects = row.get('shared_projects', 0)
        shared_files = row.get('shared_files', 0)
        
        rank += 1
        
        # Check if anonymous or no valid user_id for link
        is_anonymous = str(collab_name).lower() == 'anonymous' or user_id is None or pd.isna(user_id)
        
        if is_anonymous:
            html += f"""
            <div class="collaborator-item no-link">
                <div class="collaborator-rank">{rank}</div>
                <div class="collaborator-info">
                    <div class="collaborator-name">{collab_name}</div>
                    <div class="collaborator-metric">{shared_projects} shared projects • {shared_files:,} shared files</div>
                </div>
            </div>
            """
        else:
            profile_url = f"https://www.synapse.org/#!Profile:{int(user_id)}"
            html += f"""
            <a href="{profile_url}" target="_blank" class="collaborator-item" style="text-decoration: none;">
                <div class="collaborator-rank">{rank}</div>
                <div class="collaborator-info">
                    <div class="collaborator-name">{collab_name}</div>
                    <div class="collaborator-metric">{shared_projects} shared projects • {shared_files:,} shared files</div>
                </div>
                <svg class="external-link-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
            </a>
            """
    html += '</div>'
    return html


def generate_heatmap_html(activity_df: pd.DataFrame, year: int) -> str:
    """Generate GitHub-style activity heatmap HTML."""
    if activity_df.empty:
        return '<div class="heatmap-container animate-in"><p style="color: var(--text-secondary);">No activity data available</p></div>'
    
    # Create a dict of date -> count
    activity_dict = {}
    for _, row in activity_df.iterrows():
        date_val = row.get('activity_date') or row.get('creation_date')
        count = row.get('activity_count') or row.get('creation_count', 0)
        if date_val:
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)[:10]
            activity_dict[date_str] = int(count)
    
    # Calculate levels based on activity distribution
    if activity_dict:
        counts = list(activity_dict.values())
        max_count = max(counts)
        q1 = max_count * 0.25
        q2 = max_count * 0.5
        q3 = max_count * 0.75
    else:
        q1, q2, q3, max_count = 1, 2, 3, 4
    
    # Generate calendar grid
    from datetime import date, timedelta
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    html = '<div class="heatmap-container animate-in"><div class="heatmap-grid">'
    
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current_date = start_date
    
    # Find first Sunday
    while current_date.weekday() != 6:
        current_date -= timedelta(days=1)
    
    current_month = -1
    while current_date <= end_date:
        if current_date.month != current_month and current_date.year == year:
            if current_month != -1:
                html += '</div></div>'  # Close previous month
            current_month = current_date.month
            html += f'<div class="heatmap-month"><div class="heatmap-month-label">{months[current_month-1]}</div><div style="display: flex; gap: 3px;">'
        
        # Start a new week
        html += '<div class="heatmap-week">'
        for _ in range(7):
            date_str = current_date.strftime('%Y-%m-%d')
            count = activity_dict.get(date_str, 0)
            
            if count == 0:
                level = ''
            elif count <= q1:
                level = 'level-1'
            elif count <= q2:
                level = 'level-2'
            elif count <= q3:
                level = 'level-3'
            else:
                level = 'level-4'
            
            # Only show cells for the target year
            if current_date.year == year:
                html += f'<div class="heatmap-cell {level}" title="{date_str}: {count} activities"></div>'
            else:
                html += '<div class="heatmap-cell" style="opacity: 0;"></div>'
            
            current_date += timedelta(days=1)
        
        html += '</div>'  # Close week
    
    html += '</div></div></div>'  # Close last month and grid
    
    # Add legend
    html += '''
    <div class="heatmap-legend">
        <span>Less</span>
        <div class="heatmap-legend-cell" style="background: var(--dark-card);"></div>
        <div class="heatmap-legend-cell" style="background: rgba(0, 255, 247, 0.2);"></div>
        <div class="heatmap-legend-cell" style="background: rgba(0, 255, 247, 0.4);"></div>
        <div class="heatmap-legend-cell" style="background: rgba(0, 255, 247, 0.6);"></div>
        <div class="heatmap-legend-cell" style="background: var(--neon-cyan);"></div>
        <span>More</span>
    </div>
    </div>
    '''
    
    return html


def generate_most_active_months_html(monthly_df: pd.DataFrame) -> str:
    """Generate HTML for most active months badges."""
    if monthly_df.empty:
        return ''
    
    # Sort by active_days descending
    sorted_df = monthly_df.sort_values('active_days', ascending=False)
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    html = ''
    
    for idx, row in sorted_df.head(3).iterrows():
        month_val = row.get('month')
        if month_val:
            if hasattr(month_val, 'month'):
                month_idx = month_val.month - 1
            else:
                month_idx = int(str(month_val)[5:7]) - 1
            month_name = months[month_idx]
        else:
            month_name = 'Unknown'
        
        active_days = row.get('active_days', 0)
        is_top = (idx == sorted_df.index[0])
        
        html += f'''
        <div class="month-badge {'top' if is_top else ''}">
            <div class="month-name">{month_name}</div>
            <div class="month-stat">{active_days} active days</div>
        </div>
        '''
    
    return html


def generate_interactive_wordcloud_html(project_names: List[str], max_words: int = 60) -> str:
    """Generate an interactive D3.js word cloud from project names."""
    from collections import Counter
    import json
    
    if not project_names:
        return ""
    
    # Remove duplicates, None values, and 'None' strings
    unique_names = list(set([
        str(name).strip() for name in project_names 
        if name and str(name).strip() and str(name).strip().lower() != 'none'
    ]))
    
    # Split project names into words and create a frequency dictionary
    word_freq = Counter()
    
    # Common stop words to filter out
    stop_words = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'are', 'was', 'were', 
                  'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
                  'project', 'study', 'data', 'analysis', 'research', 'of', 'a', 'an', 'in', 'on', 'at', 'to',
                  'using', 'based', 'new', 'via', 'none', 'null', 'nan'}
    
    for name in unique_names:
        # Split on common delimiters and add individual words
        words = str(name).replace('_', ' ').replace('-', ' ').replace('.', ' ').split()
        for word in words:
            word_lower = word.lower().strip()
            # Filter out very short words, numbers, and common stop words
            if (len(word_lower) > 2 and 
                word_lower not in stop_words and 
                not word_lower.isdigit() and
                word_lower.isalpha()):
                word_freq[word_lower] += 1
    
    if not word_freq:
        return ""
    
    # Get the most common words
    top_words = word_freq.most_common(max_words)
    
    if not top_words:
        return ""
    
    # Prepare data for D3 word cloud
    max_freq = top_words[0][1]
    min_freq = top_words[-1][1] if len(top_words) > 1 else max_freq
    
    # Color palette
    colors = ['#00ffff', '#ff00ff', '#b19cd9', '#00ff88', '#ff6b6b', '#4ecdc4']
    
    word_data = []
    for i, (word, freq) in enumerate(top_words):
        word_data.append({
            'text': word.capitalize(),
            'size': freq,
            'color': colors[i % len(colors)]
        })
    
    word_data_json = json.dumps(word_data)
    
    return f'''<div id="wordcloud-container" class="animate-in"></div>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/jasondavies/d3-cloud@master/build/d3.layout.cloud.js"></script>
    <script>
        (function() {{
            const data = {word_data_json};
            const width = 1000;
            const height = 500;
            
            // Scale for font sizes
            const maxSize = data[0].size;
            const minSize = data[data.length - 1].size;
            const sizeScale = d3.scaleLinear()
                .domain([minSize, maxSize])
                .range([20, 80]);
            
            const layout = d3.layout.cloud()
                .size([width, height])
                .words(data.map(d => ({{
                    text: d.text,
                    size: sizeScale(d.size),
                    color: d.color
                }})))
                .padding(5)
                .rotate(() => ~~(Math.random() * 2) * 90)  // 0 or 90 degrees
                .font("Orbitron, sans-serif")
                .fontSize(d => d.size)
                .on("end", draw);
            
            layout.start();
            
            function draw(words) {{
                const svg = d3.select("#wordcloud-container")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
                
                const text = svg.selectAll("text")
                    .data(words)
                    .enter().append("text")
                    .style("font-size", d => d.size + "px")
                    .style("font-family", "Orbitron, sans-serif")
                    .style("font-weight", "600")
                    .style("fill", d => d.color)
                    .attr("text-anchor", "middle")
                    .attr("transform", d => "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")")
                    .text(d => d.text)
                    .style("cursor", "pointer")
                    .on("mouseover", function(event, d) {{
                        d3.select(this)
                            .transition()
                            .duration(200)
                            .style("font-size", (d.size * 1.3) + "px")
                            .style("filter", "drop-shadow(0 0 8px " + d.color + ")");
                    }})
                    .on("mouseout", function(event, d) {{
                        d3.select(this)
                            .transition()
                            .duration(200)
                            .style("font-size", d.size + "px")
                            .style("filter", "none");
                    }})
                    .append("title")
                    .text(d => {{
                        const wordData = data.find(w => w.text.toLowerCase() === d.text.toLowerCase());
                        return wordData ? wordData.size + " occurrence" + (wordData.size > 1 ? "s" : "") : "";
                    }});
            }}
        }})();
    </script>'''


def generate_badges_html(project_count: int, percentile_rank: float, 
                         controlled_projects: int, open_projects: int,
                         night_owl_score: float, early_bird_score: float,
                         file_count: int = 0, total_size_gb: float = 0,
                         active_days: int = 0, weekend_score: float = 0,
                         total_creations: int = 0, files_created: int = 0,
                         comparison_ratio: float = 1.0, busiest_day_downloads: int = 0,
                         collaborator_count: int = 0) -> str:
    """Generate HTML for achievement badges with varied criteria."""
    badges = []
    
    # Data Explorer Badge (10+ projects)
    if project_count >= 10:
        badges.append({
            'icon': '🔭',
            'title': 'Data Explorer',
            'description': f'Explored {project_count} unique projects this year',
            'earned': True,
            'special': project_count >= 50
        })
    elif project_count >= 5:
        badges.append({
            'icon': '🔍',
            'title': 'Project Scout',
            'description': f'Discovered {project_count} unique projects',
            'earned': True,
            'special': False
        })
    
    # Power User Badge (top percentile)
    if percentile_rank <= 5:
        badges.append({
            'icon': '⚡',
            'title': 'Power User',
            'description': f'Top {percentile_rank:.0f}% of all Synapse downloaders',
            'earned': True,
            'special': True
        })
    elif percentile_rank <= 10:
        badges.append({
            'icon': '🚀',
            'title': 'Heavy User',
            'description': f'Top {percentile_rank:.0f}% of Synapse users',
            'earned': True,
            'special': False
        })
    elif percentile_rank <= 25:
        badges.append({
            'icon': '📊',
            'title': 'Active Researcher',
            'description': f'Top {percentile_rank:.0f}% of Synapse users',
            'earned': True,
            'special': False
        })
    
    # Access Level Badge
    total_access = controlled_projects + open_projects
    if total_access > 0:
        controlled_ratio = controlled_projects / total_access
        if controlled_ratio >= 0.7:
            badges.append({
                'icon': '🔐',
                'title': 'Sensitive Data Superstar',
                'description': f'Trusted with controlled-access data from {controlled_projects} projects',
                'earned': True,
                'special': True
            })
        elif controlled_ratio >= 0.5:
            badges.append({
                'icon': '🛡️',
                'title': 'Data Guardian',
                'description': f'Access to {controlled_projects} controlled-access projects',
                'earned': True,
                'special': False
            })
        elif open_projects >= 20:
            badges.append({
                'icon': '🌐',
                'title': 'Open Data Evangelist',
                'description': f'Champion of open science with {open_projects} open-access projects',
                'earned': True,
                'special': open_projects >= 50
            })
        elif open_projects >= 10:
            badges.append({
                'icon': '📖',
                'title': 'Open Science Advocate',
                'description': f'Supports open science with {open_projects} open projects',
                'earned': True,
                'special': False
            })
    
    # Time-based badges
    if night_owl_score >= 50:
        badges.append({
            'icon': '🦉',
            'title': 'Night Owl',
            'description': f'{night_owl_score:.0f}% of downloads after hours',
            'earned': True,
            'special': night_owl_score >= 70
        })
    elif night_owl_score >= 30:
        badges.append({
            'icon': '🌙',
            'title': 'Evening Explorer',
            'description': f'{night_owl_score:.0f}% of activity after 6pm',
            'earned': True,
            'special': False
        })
    
    if early_bird_score >= 25:
        badges.append({
            'icon': '🐦',
            'title': 'Early Bird',
            'description': f'{early_bird_score:.0f}% of downloads before 9am',
            'earned': True,
            'special': early_bird_score >= 40
        })
    elif early_bird_score >= 15:
        badges.append({
            'icon': '🌅',
            'title': 'Morning Person',
            'description': f'{early_bird_score:.0f}% of activity before 9am',
            'earned': True,
            'special': False
        })
    
    # Weekend warrior badge
    if weekend_score >= 40:
        badges.append({
            'icon': '🏖️',
            'title': 'Weekend Warrior',
            'description': f'{weekend_score:.0f}% of downloads on weekends',
            'earned': True,
            'special': weekend_score >= 50
        })
    elif weekend_score >= 25:
        badges.append({
            'icon': '📅',
            'title': 'Flexible Schedule',
            'description': f'{weekend_score:.0f}% weekend activity',
            'earned': True,
            'special': False
        })
    
    # File download badges
    if file_count >= 10000:
        badges.append({
            'icon': '📦',
            'title': 'Data Hoarder',
            'description': f'Downloaded {file_count:,} files this year',
            'earned': True,
            'special': file_count >= 50000
        })
    elif file_count >= 5000:
        badges.append({
            'icon': '📚',
            'title': 'Data Collector',
            'description': f'Downloaded {file_count:,} files',
            'earned': True,
            'special': False
        })
    elif file_count >= 1000:
        badges.append({
            'icon': '📥',
            'title': 'Active Downloader',
            'description': f'Downloaded {file_count:,} files',
            'earned': True,
            'special': False
        })
    
    # Data size badges
    if total_size_gb >= 1000:
        badges.append({
            'icon': '💾',
            'title': 'Terabyte Titan',
            'description': f'Downloaded {total_size_gb:.1f} TB of data',
            'earned': True,
            'special': total_size_gb >= 5000
        })
    elif total_size_gb >= 500:
        badges.append({
            'icon': '🗄️',
            'title': 'Data Archivist',
            'description': f'Downloaded {total_size_gb:.1f} GB of data',
            'earned': True,
            'special': False
        })
    elif total_size_gb >= 100:
        badges.append({
            'icon': '💿',
            'title': 'Data Enthusiast',
            'description': f'Downloaded {total_size_gb:.1f} GB',
            'earned': True,
            'special': False
        })
    
    # Activity consistency badges
    if active_days >= 300:
        badges.append({
            'icon': '🔥',
            'title': 'Daily Dedication',
            'description': f'Active {active_days} days this year',
            'earned': True,
            'special': active_days >= 350
        })
    elif active_days >= 200:
        badges.append({
            'icon': '📆',
            'title': 'Consistent Contributor',
            'description': f'Active {active_days} days',
            'earned': True,
            'special': False
        })
    elif active_days >= 100:
        badges.append({
            'icon': '✅',
            'title': 'Regular User',
            'description': f'Active {active_days} days',
            'earned': True,
            'special': False
        })
    
    # Creation badges
    if total_creations >= 1000:
        badges.append({
            'icon': '🏗️',
            'title': 'Content Creator',
            'description': f'Created {total_creations:,} items on Synapse',
            'earned': True,
            'special': total_creations >= 5000
        })
    elif total_creations >= 500:
        badges.append({
            'icon': '✏️',
            'title': 'Active Creator',
            'description': f'Created {total_creations:,} items',
            'earned': True,
            'special': False
        })
    elif total_creations >= 100:
        badges.append({
            'icon': '📝',
            'title': 'Contributor',
            'description': f'Created {total_creations:,} items',
            'earned': True,
            'special': False
        })
    
    if files_created >= 1000:
        badges.append({
            'icon': '📄',
            'title': 'File Factory',
            'description': f'Created {files_created:,} files',
            'earned': True,
            'special': files_created >= 5000
        })
    
    # File size preference badges
    if comparison_ratio >= 2.0:
        badges.append({
            'icon': '🐋',
            'title': 'Big Data Lover',
            'description': f'Prefers files {comparison_ratio:.1f}x larger than average',
            'earned': True,
            'special': comparison_ratio >= 3.0
        })
    elif comparison_ratio <= 0.5:
        badges.append({
            'icon': '⚡',
            'title': 'Lightweight Champion',
            'description': 'Prefers smaller, efficient files',
            'earned': True,
            'special': comparison_ratio <= 0.3
        })
    
    # Busiest day badge
    if busiest_day_downloads >= 1000:
        badges.append({
            'icon': '💥',
            'title': 'Power Session',
            'description': f'Peak day: {busiest_day_downloads:,} downloads',
            'earned': True,
            'special': busiest_day_downloads >= 5000
        })
    elif busiest_day_downloads >= 500:
        badges.append({
            'icon': '📈',
            'title': 'Intense Day',
            'description': f'Peak day: {busiest_day_downloads:,} downloads',
            'earned': True,
            'special': False
        })
    
    # Collaboration badges
    if collaborator_count >= 20:
        badges.append({
            'icon': '🤝',
            'title': 'Social Butterfly',
            'description': f'Connected with {collaborator_count} researchers',
            'earned': True,
            'special': collaborator_count >= 50
        })
    elif collaborator_count >= 10:
        badges.append({
            'icon': '👥',
            'title': 'Team Player',
            'description': f'Connected with {collaborator_count} researchers',
            'earned': True,
            'special': False
        })
    elif collaborator_count >= 5:
        badges.append({
            'icon': '🔗',
            'title': 'Network Builder',
            'description': f'Connected with {collaborator_count} researchers',
            'earned': True,
            'special': False
        })
    
    # Generate HTML
    if not badges:
        return '<p style="color: var(--text-secondary);">Keep exploring to earn badges!</p>'
    
    html = ''
    for badge in badges:
        special_class = 'special' if badge.get('special') else 'earned'
        html += f'''
        <div class="badge {special_class}">
            <div class="badge-icon">{badge['icon']}</div>
            <div class="badge-title">{badge['title']}</div>
            <div class="badge-description">{badge['description']}</div>
        </div>
        '''
    
    return html


def generate_network_data(network_df: pd.DataFrame, collaborators_df: pd.DataFrame, 
                          user_id: int, user_name: str) -> dict:
    """Generate D3.js compatible network data."""
    nodes = []
    links = []
    
    # Add center node (current user)
    nodes.append({
        'id': str(user_id),
        'name': user_name,
        'isCenter': True,
        'sharedFiles': 0,
        'profileUrl': f'https://www.synapse.org/#!Profile:{user_id}'
    })
    
    if collaborators_df.empty:
        return {'nodes': nodes, 'links': []}
    
    # Get top collaborators for the network
    top_collabs = collaborators_df.head(20)
    
    for idx, row in top_collabs.iterrows():
        collab_id = row.get('user_id')
        if collab_id is None or pd.isna(collab_id):
            continue
            
        collab_name = row.get('collaborator_name', f'User {collab_id}')
        shared_files = row.get('shared_files', 0)
        
        is_anonymous = str(collab_name).lower() == 'anonymous'
        
        nodes.append({
            'id': str(int(collab_id)),
            'name': collab_name,
            'isCenter': False,
            'showLabel': idx < 5,  # Show labels for top 5
            'sharedFiles': int(shared_files),
            'profileUrl': None if is_anonymous else f'https://www.synapse.org/#!Profile:{int(collab_id)}'
        })
        
        links.append({
            'source': str(user_id),
            'target': str(int(collab_id)),
            'weight': int(shared_files)
        })
    
    return {'nodes': nodes, 'links': links}


def generate_wrapped(
    username: str,
    year: Optional[int] = None,
    output_path: Optional[str] = None,
    snowflake_config: Optional[Dict] = None,
    include_audio: bool = True,
    timezone: str = 'America/Chicago'
) -> str:
    """
    Generate a Synapse Wrapped visualization for a single user.
    
    Args:
        username: Username or email of the Synapse user
        year: Year to analyze (defaults to current year)
        output_path: Path to save the HTML file (defaults to username_wrapped_{year}.html)
        snowflake_config: Snowflake connection config dict (if None, uses streamlit secrets)
        include_audio: Whether to include background music in HTML
    
    Returns:
        Path to the generated HTML file
    """
    if year is None:
        year = datetime.now().year
    
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Get user ID from username
    user_query = get_user_id_from_username(username)
    user_df = get_data_from_snowflake(user_query, snowflake_config)
    
    if user_df.empty:
        raise ValueError(f"User '{username}' not found in Synapse")
    
    # Handle different possible column names (case-insensitive)
    user_id_col = None
    for col in user_df.columns:
        if col.lower() == 'user_id':
            user_id_col = col
            break
    
    if user_id_col is None:
        raise ValueError(f"Could not find user_id column in query result. Columns: {list(user_df.columns)}")
    
    user_id = int(user_df.iloc[0][user_id_col])
    
    # Get user name (try different possible column names)
    user_name_col = None
    for col in user_df.columns:
        if col.lower() in ['user_name', 'username']:
            user_name_col = col
            break
    
    user_name = user_df.iloc[0].get(user_name_col, username) if user_name_col else username
    
    # Collect all data
    print(f"Collecting data for user {user_name} (ID: {user_id})...")
    
    # Files downloaded
    files_query = query_user_files_downloaded(user_id, start_date, end_date)
    files_df = get_data_from_snowflake(files_query, snowflake_config)
    files_df.columns = files_df.columns.str.lower()
    file_count = int(files_df.iloc[0]['file_count']) if not files_df.empty and 'file_count' in files_df.columns else 0
    total_size = int(files_df.iloc[0]['total_size_bytes']) if not files_df.empty and 'total_size_bytes' in files_df.columns else 0
    
    # Top projects (now top 10, filtering invalid ones)
    top_projects_query = query_user_top_projects(user_id, start_date, end_date, limit=15)  # Get extra to filter
    top_projects_df = get_data_from_snowflake(top_projects_query, snowflake_config)
    top_projects_df.columns = top_projects_df.columns.str.lower()
    
    # All projects for word cloud
    all_projects_query = query_user_all_projects(user_id, start_date, end_date)
    all_projects_df = get_data_from_snowflake(all_projects_query, snowflake_config)
    all_projects_df.columns = all_projects_df.columns.str.lower()
    project_count = len(all_projects_df)
    project_names = all_projects_df['project_name'].dropna().tolist() if 'project_name' in all_projects_df.columns else []
    
    # Active days
    active_days_query = query_user_active_days(user_id, start_date, end_date)
    active_days_df = get_data_from_snowflake(active_days_query, snowflake_config)
    active_days_df.columns = active_days_df.columns.str.lower()
    active_days = int(active_days_df.iloc[0]['active_days']) if not active_days_df.empty and 'active_days' in active_days_df.columns else 0
    
    # Activity by date for heatmap
    activity_query = query_user_activity_by_date(user_id, start_date, end_date)
    activity_df = get_data_from_snowflake(activity_query, snowflake_config)
    activity_df.columns = activity_df.columns.str.lower()
    
    # Activity by month
    monthly_query = query_user_activity_by_month(user_id, start_date, end_date)
    monthly_df = get_data_from_snowflake(monthly_query, snowflake_config)
    monthly_df.columns = monthly_df.columns.str.lower()
    
    # Creations
    creations_query = query_user_creations(user_id, start_date, end_date)
    creations_df = get_data_from_snowflake(creations_query, snowflake_config)
    creations_df.columns = creations_df.columns.str.lower()
    
    # Collaboration network
    network_query = query_user_collaboration_network(user_id, start_date, end_date)
    network_df = get_data_from_snowflake(network_query, snowflake_config)
    network_df.columns = network_df.columns.str.lower()
    
    # Top collaborators (now top 10)
    collaborators_query = query_user_top_collaborators(user_id, start_date, end_date, limit=10)
    collaborators_df = get_data_from_snowflake(collaborators_query, snowflake_config)
    collaborators_df.columns = collaborators_df.columns.str.lower()
    
    # Hourly activity for radial chart (in user's timezone)
    hourly_query = query_user_activity_by_hour(user_id, start_date, end_date, timezone=timezone)
    hourly_df = get_data_from_snowflake(hourly_query, snowflake_config)
    hourly_df.columns = hourly_df.columns.str.lower()
    
    # Time patterns (night owl, early bird, weekend) in user's timezone
    time_patterns_query = query_user_time_patterns(user_id, start_date, end_date, timezone=timezone)
    time_patterns_df = get_data_from_snowflake(time_patterns_query, snowflake_config)
    time_patterns_df.columns = time_patterns_df.columns.str.lower()
    
    # First download of the year
    first_download_query = query_user_first_download(user_id, start_date, end_date)
    first_download_df = get_data_from_snowflake(first_download_query, snowflake_config)
    first_download_df.columns = first_download_df.columns.str.lower()
    
    # Busiest day
    busiest_day_query = query_user_busiest_day(user_id, start_date, end_date)
    busiest_day_df = get_data_from_snowflake(busiest_day_query, snowflake_config)
    busiest_day_df.columns = busiest_day_df.columns.str.lower()
    
    # Largest download
    largest_download_query = query_user_largest_download(user_id, start_date, end_date)
    largest_download_df = get_data_from_snowflake(largest_download_query, snowflake_config)
    largest_download_df.columns = largest_download_df.columns.str.lower()
    
    # Platform average file size
    platform_avg_query = query_platform_average_file_size(start_date, end_date)
    platform_avg_df = get_data_from_snowflake(platform_avg_query, snowflake_config)
    platform_avg_df.columns = platform_avg_df.columns.str.lower()
    
    # User average file size
    user_avg_query = query_user_average_file_size(user_id, start_date, end_date)
    user_avg_df = get_data_from_snowflake(user_avg_query, snowflake_config)
    user_avg_df.columns = user_avg_df.columns.str.lower()
    
    # Monthly download size for growth chart
    monthly_size_query = query_user_monthly_download_size(user_id, start_date, end_date)
    monthly_size_df = get_data_from_snowflake(monthly_size_query, snowflake_config)
    monthly_size_df.columns = monthly_size_df.columns.str.lower()
    
    # Power user ranking
    ranking_query = query_platform_download_ranking(user_id, start_date, end_date)
    ranking_df = get_data_from_snowflake(ranking_query, snowflake_config)
    ranking_df.columns = ranking_df.columns.str.lower()
    
    # Access requirements
    access_req_query = query_user_access_requirements(user_id, start_date, end_date)
    access_req_df = get_data_from_snowflake(access_req_query, snowflake_config)
    access_req_df.columns = access_req_df.columns.str.lower()
    
    # Process new data for additional slides
    from synapse_wrapped.visualizations import format_bytes
    
    # Hourly data for radial chart
    hourly_data = []
    if not hourly_df.empty:
        for _, row in hourly_df.iterrows():
            hourly_data.append({'hour': int(row.get('hour_of_day', 0)), 'count': int(row.get('download_count', 0))})
    
    # Monthly growth data
    monthly_growth_data = []
    if not monthly_size_df.empty:
        for _, row in monthly_size_df.iterrows():
            month_val = row.get('month')
            if month_val:
                month_str = month_val.strftime('%Y-%m-%d') if hasattr(month_val, 'strftime') else str(month_val)
                monthly_growth_data.append({'month': month_str, 'size': int(row.get('total_size_bytes', 0) or 0)})
    
    # Time pattern metrics
    total_downloads_tp = 1
    night_downloads = early_downloads = weekend_downloads = weekday_downloads = 0
    if not time_patterns_df.empty:
        total_downloads_tp = int(time_patterns_df.iloc[0].get('total_downloads', 1)) or 1
        night_downloads = int(time_patterns_df.iloc[0].get('night_downloads', 0) or 0)
        early_downloads = int(time_patterns_df.iloc[0].get('early_downloads', 0) or 0)
        weekend_downloads = int(time_patterns_df.iloc[0].get('weekend_downloads', 0) or 0)
    
    night_owl_score = round((night_downloads / total_downloads_tp) * 100, 1)
    early_bird_score = round((early_downloads / total_downloads_tp) * 100, 1)
    weekend_score = round((weekend_downloads / total_downloads_tp) * 100, 1)
    night_owl_class = 'highlight' if night_owl_score > 30 else ''
    early_bird_class = 'highlight' if early_bird_score > 15 else ''
    weekend_class = 'highlight' if weekend_score > 30 else ''
    
    # First download info
    first_download_date, first_download_file, first_download_project = "N/A", "Unknown", "Unknown project"
    if not first_download_df.empty:
        fd_date = first_download_df.iloc[0].get('first_download_date')
        if fd_date:
            first_download_date = fd_date.strftime('%B %d, %Y') if hasattr(fd_date, 'strftime') else str(fd_date)[:10]
        first_download_file = str(first_download_df.iloc[0].get('file_name', 'Unknown'))[:50]
        first_download_project = str(first_download_df.iloc[0].get('project_name', 'Unknown project'))[:40]
    
    # Busiest day info
    busiest_day_date, busiest_day_downloads, busiest_day_size = "N/A", 0, "0 B"
    if not busiest_day_df.empty:
        bd_date = busiest_day_df.iloc[0].get('busiest_date')
        if bd_date:
            busiest_day_date = bd_date.strftime('%B %d') if hasattr(bd_date, 'strftime') else str(bd_date)[:10]
        busiest_day_downloads = int(busiest_day_df.iloc[0].get('download_count', 0) or 0)
        busiest_day_size = format_bytes(int(busiest_day_df.iloc[0].get('total_size_bytes', 0) or 0))
    
    # Largest download info
    largest_file_size, largest_file_name, largest_file_project = "N/A", "Unknown", ""
    if not largest_download_df.empty:
        lf_size = largest_download_df.iloc[0].get('content_size', 0)
        if lf_size:
            largest_file_size = format_bytes(int(lf_size))
        largest_file_name = str(largest_download_df.iloc[0].get('file_name', 'Unknown'))[:60]
        largest_file_project = str(largest_download_df.iloc[0].get('project_name', ''))[:40]
    
    # Average file sizes comparison
    platform_avg = float(platform_avg_df.iloc[0].get('avg_file_size', 0) or 0) if not platform_avg_df.empty else 0
    user_avg = float(user_avg_df.iloc[0].get('avg_file_size', 0) or 0) if not user_avg_df.empty else 0
    platform_avg_size = format_bytes(int(platform_avg)) if platform_avg else "N/A"
    user_avg_size = format_bytes(int(user_avg)) if user_avg else "N/A"
    
    if platform_avg > 0:
        comparison_ratio = user_avg / platform_avg
        comparison_percent = min(comparison_ratio * 50, 100)
        if comparison_ratio > 1.5:
            size_comparison_text = f"You download {comparison_ratio:.1f}x larger files than average! 🐋"
        elif comparison_ratio > 0.7:
            size_comparison_text = "You're right around the platform average"
        else:
            size_comparison_text = "You prefer smaller, lighter files"
    else:
        comparison_percent, size_comparison_text = 50, "Platform comparison unavailable"
        comparison_ratio = 1.0
    
    # Power user ranking and access badges
    percentile_rank = float(ranking_df.iloc[0].get('percentile_rank', 1.0) or 1.0) * 100 if not ranking_df.empty else 100.0
    controlled_projects = int(access_req_df.iloc[0].get('controlled_projects', 0) or 0) if not access_req_df.empty else 0
    open_projects = int(access_req_df.iloc[0].get('open_projects', 0) or 0) if not access_req_df.empty else 0
    
    # Generate component HTML for the new template
    top_projects_html = generate_top_projects_html(top_projects_df.head(10))
    top_collaborators_html = generate_top_collaborators_html(collaborators_df)
    heatmap_html = generate_heatmap_html(activity_df, year)
    most_active_months_html = generate_most_active_months_html(monthly_df)
    
    # Interactive word cloud
    wordcloud_html = generate_interactive_wordcloud_html(project_names, max_words=60)
    
    # Network data for D3.js
    network_data = generate_network_data(network_df, collaborators_df, user_id, user_name)
    
    # Creation stats - properly sum all node types
    count_col = None
    type_col = None
    for col in creations_df.columns:
        if 'count' in col.lower() or 'creation' in col.lower():
            count_col = col
        if 'type' in col.lower() or 'node' in col.lower():
            type_col = col
    
    projects_created = 0
    files_created = 0
    tables_created = 0
    folders_created = 0
    other_created = 0
    
    if type_col and count_col and not creations_df.empty:
        for _, row in creations_df.iterrows():
            node_type = str(row[type_col]).lower()
            count = int(row[count_col])
            if node_type == 'project':
                projects_created = count
            elif node_type == 'file':
                files_created = count
            elif node_type == 'table':
                tables_created = count
            elif node_type == 'folder':
                folders_created = count
            else:
                other_created += count
    
    # Total creations is the actual sum
    total_creations = projects_created + files_created + tables_created + folders_created + other_created
    
    # Calculate total size in GB for badges
    total_size_gb = total_size / (1024 ** 3) if total_size > 0 else 0
    
    # Get collaborator count
    collaborator_count = len(collaborators_df) if not collaborators_df.empty else 0
    
    # Generate badges (after all data is calculated)
    badges_html = generate_badges_html(
        project_count=project_count,
        percentile_rank=percentile_rank,
        controlled_projects=controlled_projects,
        open_projects=open_projects,
        night_owl_score=night_owl_score,
        early_bird_score=early_bird_score,
        file_count=file_count,
        total_size_gb=total_size_gb,
        active_days=active_days,
        weekend_score=weekend_score,
        total_creations=total_creations,
        files_created=files_created,
        comparison_ratio=comparison_ratio,
        busiest_day_downloads=busiest_day_downloads,
        collaborator_count=collaborator_count
    )
    
    # Calculate active percentage (out of 365 days)
    active_percentage = round((active_days / 365) * 100, 1)
    
    # Format file count and total size
    from synapse_wrapped.visualizations import format_bytes
    total_size_str = format_bytes(total_size)
    
    # Generate HTML using template
    template = get_html_template()
    
    # Replace all placeholders
    html_content = template.replace("{year}", str(year))
    html_content = html_content.replace("{username}", str(user_name))
    html_content = html_content.replace("{file_count}", f"{file_count:,}")
    html_content = html_content.replace("{total_size}", total_size_str)
    html_content = html_content.replace("{active_days}", str(active_days))
    html_content = html_content.replace("{active_percentage}", str(active_percentage))
    html_content = html_content.replace("{project_count}", str(project_count))
    html_content = html_content.replace("{wordcloud_html}", wordcloud_html)
    html_content = html_content.replace("{top_projects_html}", top_projects_html)
    html_content = html_content.replace("{total_creations}", f"{total_creations:,}")
    html_content = html_content.replace("{projects_created}", str(projects_created))
    html_content = html_content.replace("{files_created}", f"{files_created:,}")
    html_content = html_content.replace("{tables_created}", str(tables_created))
    html_content = html_content.replace("{folders_created}", str(folders_created))
    html_content = html_content.replace("{top_collaborators_html}", top_collaborators_html)
    html_content = html_content.replace("{heatmap_html}", heatmap_html)
    html_content = html_content.replace("{most_active_months_html}", most_active_months_html)
    html_content = html_content.replace("{network_data_json}", json.dumps(network_data))
    html_content = html_content.replace("{generation_date}", datetime.now().strftime("%B %d, %Y"))
    
    # New placeholders for additional slides
    html_content = html_content.replace("{hourly_data_json}", json.dumps(hourly_data))
    html_content = html_content.replace("{monthly_growth_json}", json.dumps(monthly_growth_data))
    html_content = html_content.replace("{night_owl_score}", str(night_owl_score))
    html_content = html_content.replace("{early_bird_score}", str(early_bird_score))
    html_content = html_content.replace("{weekend_score}", str(weekend_score))
    html_content = html_content.replace("{night_owl_class}", night_owl_class)
    html_content = html_content.replace("{early_bird_class}", early_bird_class)
    html_content = html_content.replace("{weekend_class}", weekend_class)
    html_content = html_content.replace("{first_download_date}", first_download_date)
    html_content = html_content.replace("{first_download_file}", first_download_file)
    html_content = html_content.replace("{first_download_project}", first_download_project)
    html_content = html_content.replace("{busiest_day_date}", busiest_day_date)
    html_content = html_content.replace("{busiest_day_downloads}", str(busiest_day_downloads))
    html_content = html_content.replace("{busiest_day_size}", busiest_day_size)
    html_content = html_content.replace("{largest_file_size}", largest_file_size)
    html_content = html_content.replace("{largest_file_name}", largest_file_name)
    html_content = html_content.replace("{largest_file_project}", largest_file_project)
    html_content = html_content.replace("{platform_avg_size}", platform_avg_size)
    html_content = html_content.replace("{user_avg_size}", user_avg_size)
    html_content = html_content.replace("{comparison_percent}", str(int(comparison_percent)))
    html_content = html_content.replace("{size_comparison_text}", size_comparison_text)
    html_content = html_content.replace("{badges_html}", badges_html)
    
    # Create a friendly timezone display name
    timezone_display = timezone.replace('_', ' ').replace('America/', '').replace('Europe/', '').replace('Asia/', '')
    html_content = html_content.replace("{timezone_display}", timezone_display)
    
    # Save to file
    if output_path is None:
        safe_username = username.replace("@", "_at_").replace(".", "_")
        output_path = f"{safe_username}_wrapped_{year}.html"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Synapse Wrapped generated: {output_path}")
    return str(output_path)


def generate_wrapped_batch(
    usernames: List[str],
    year: Optional[int] = None,
    output_dir: Optional[str] = None,
    snowflake_config: Optional[Dict] = None,
    include_audio: bool = True
) -> List[str]:
    """
    Generate Synapse Wrapped visualizations for multiple users.
    
    Args:
        usernames: List of usernames or emails
        year: Year to analyze (defaults to current year)
        output_dir: Directory to save HTML files (defaults to 'wrapped_output')
        snowflake_config: Snowflake connection config dict
        include_audio: Whether to include background music in HTML
    
    Returns:
        List of paths to generated HTML files
    """
    if output_dir is None:
        output_dir = "wrapped_output"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for username in usernames:
        try:
            safe_username = username.replace("@", "_at_").replace(".", "_")
            output_path = output_dir / f"{safe_username}_wrapped_{year or datetime.now().year}.html"
            
            file_path = generate_wrapped(
                username=username,
                year=year,
                output_path=str(output_path),
                snowflake_config=snowflake_config,
                include_audio=include_audio
            )
            generated_files.append(file_path)
        except Exception as e:
            print(f"Error generating wrapped for {username}: {e}")
            continue
    
    print(f"\nGenerated {len(generated_files)} wrapped visualizations in {output_dir}")
    return generated_files
