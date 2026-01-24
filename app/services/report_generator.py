from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from io import BytesIO
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class WorkoutReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )
    
    def generate_report(self, analysis_results: Dict[str, Any]) -> BytesIO:
        """
        Generate comprehensive PDF workout analysis report
        
        Args:
            analysis_results: Dictionary containing analysis results
            
        Returns:
            BytesIO object containing the PDF report
        """
        try:
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story (content)
            story = []
            
            # Title
            story.append(Paragraph("Workout Analysis Report", self.title_style))
            story.append(Spacer(1, 20))
            
            # Session Information
            story.extend(self._create_session_info(analysis_results))
            story.append(Spacer(1, 20))
            
            # Performance Summary
            story.extend(self._create_performance_summary(analysis_results))
            story.append(Spacer(1, 20))
            
            # Detailed Analysis
            story.extend(self._create_detailed_analysis(analysis_results))
            story.append(Spacer(1, 20))
            
            # Form Feedback
            story.extend(self._create_form_feedback(analysis_results))
            story.append(Spacer(1, 20))
            
            # Mistakes and Improvements
            story.extend(self._create_mistakes_section(analysis_results))
            story.append(Spacer(1, 20))
            
            # Timeline Summary
            story.extend(self._create_timeline_summary(analysis_results))
            story.append(Spacer(1, 20))
            
            # Recommendations
            story.extend(self._create_recommendations(analysis_results))
            
            # Build PDF
            doc.build(story)
            
            # Reset buffer position
            buffer.seek(0)
            
            logger.info("PDF report generated successfully")
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def _create_session_info(self, results: Dict[str, Any]) -> List:
        """Create session information section"""
        content = []
        
        content.append(Paragraph("Session Information", self.heading_style))
        
        session_data = [
            ['Exercise Type:', results.get('exercise_name', 'Unknown').replace('_', ' ').title()],
            ['Session Date:', datetime.now().strftime('%B %d, %Y')],
            ['Duration:', f"{results.get('duration', 0):.1f} seconds"],
            ['Total Frames Analyzed:', str(results.get('processed_frames', 0))],
            ['Analysis Quality:', 'High' if results.get('processed_frames', 0) > 100 else 'Medium']
        ]
        
        table = Table(session_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
        ]))
        
        content.append(table)
        return content
    
    def _create_performance_summary(self, results: Dict[str, Any]) -> List:
        """Create performance summary section"""
        content = []
        
        content.append(Paragraph("Performance Summary", self.heading_style))
        
        # Calculate metrics
        total_reps = results.get('total_reps', 0)
        correct_reps = results.get('correct_reps', 0)
        accuracy_score = results.get('accuracy_score', 0) * 100
        calories_burned = results.get('calories_burned', 0)
        
        # Performance rating
        if accuracy_score >= 90:
            rating = "Excellent"
            rating_color = colors.green
        elif accuracy_score >= 80:
            rating = "Good"
            rating_color = colors.blue
        elif accuracy_score >= 70:
            rating = "Fair"
            rating_color = colors.orange
        else:
            rating = "Needs Improvement"
            rating_color = colors.red
        
        summary_data = [
            ['Total Repetitions:', str(total_reps)],
            ['Correct Form Reps:', str(correct_reps)],
            ['Overall Accuracy:', f"{accuracy_score:.1f}%"],
            ['Calories Burned:', f"{calories_burned:.1f}"],
            ['Performance Rating:', rating]
        ]
        
        table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -2), colors.black),
            ('TEXTCOLOR', (1, -1), (1, -1), rating_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
            ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2980b9'))
        ]))
        
        content.append(table)
        return content
    
    def _create_detailed_analysis(self, results: Dict[str, Any]) -> List:
        """Create detailed analysis section"""
        content = []
        
        content.append(Paragraph("Detailed Analysis", self.heading_style))
        
        # Rep accuracy breakdown
        total_reps = results.get('total_reps', 0)
        correct_reps = results.get('correct_reps', 0)
        
        if total_reps > 0:
            rep_accuracy = (correct_reps / total_reps) * 100
            incorrect_reps = total_reps - correct_reps
            
            content.append(Paragraph(f"<b>Repetition Analysis:</b>", self.body_style))
            content.append(Paragraph(f"• {correct_reps} out of {total_reps} repetitions performed with correct form ({rep_accuracy:.1f}%)", self.body_style))
            
            if incorrect_reps > 0:
                content.append(Paragraph(f"• {incorrect_reps} repetitions need form improvement", self.body_style))
        
        # Timeline analysis
        timeline_data = results.get('analysis_timeline', [])
        if timeline_data:
            content.append(Paragraph(f"<b>Workout Progression:</b>", self.body_style))
            content.append(Paragraph(f"• Analysis captured {len(timeline_data)} key moments during your workout", self.body_style))
            
            # Find best and worst performing moments
            if len(timeline_data) > 1:
                best_moment = max(timeline_data, key=lambda x: x.get('accuracy_score', 0))
                worst_moment = min(timeline_data, key=lambda x: x.get('accuracy_score', 1))
                
                content.append(Paragraph(f"• Best form at {best_moment.get('timestamp', 0):.1f}s with {best_moment.get('accuracy_score', 0)*100:.1f}% accuracy", self.body_style))
                content.append(Paragraph(f"• Form needs attention around {worst_moment.get('timestamp', 0):.1f}s", self.body_style))
        
        return content
    
    def _create_form_feedback(self, results: Dict[str, Any]) -> List:
        """Create form feedback section"""
        content = []
        
        feedback_list = results.get('form_feedback', [])
        if feedback_list:
            content.append(Paragraph("Form Feedback", self.heading_style))
            
            # Remove duplicates and categorize feedback
            unique_feedback = list(set(feedback_list))
            
            for feedback in unique_feedback[:10]:  # Limit to top 10 feedback items
                content.append(Paragraph(f"• {feedback}", self.body_style))
        
        return content
    
    def _create_mistakes_section(self, results: Dict[str, Any]) -> List:
        """Create mistakes and improvements section"""
        content = []
        
        mistakes = results.get('mistakes', [])
        if mistakes:
            content.append(Paragraph("Areas for Improvement", self.heading_style))
            
            # Group mistakes by severity
            high_severity = [m for m in mistakes if m.get('severity') == 'high']
            medium_severity = [m for m in mistakes if m.get('severity') == 'medium']
            low_severity = [m for m in mistakes if m.get('severity') == 'low']
            
            if high_severity:
                content.append(Paragraph("<b>High Priority Issues:</b>", self.body_style))
                for mistake in high_severity[:3]:  # Top 3 high priority
                    timestamp = mistake.get('timestamp', 0)
                    description = mistake.get('description', 'Unknown issue')
                    content.append(Paragraph(f"• At {timestamp:.1f}s: {description}", self.body_style))
            
            if medium_severity:
                content.append(Paragraph("<b>Medium Priority Issues:</b>", self.body_style))
                for mistake in medium_severity[:3]:  # Top 3 medium priority
                    timestamp = mistake.get('timestamp', 0)
                    description = mistake.get('description', 'Unknown issue')
                    content.append(Paragraph(f"• At {timestamp:.1f}s: {description}", self.body_style))
        
        return content
    
    def _create_timeline_summary(self, results: Dict[str, Any]) -> List:
        """Create timeline summary section"""
        content = []
        
        timeline_data = results.get('analysis_timeline', [])
        if len(timeline_data) > 5:  # Only show if we have enough data points
            content.append(Paragraph("Workout Timeline Highlights", self.heading_style))
            
            # Show key moments (every 20% of the workout)
            total_duration = results.get('duration', 0)
            if total_duration > 0:
                intervals = [0.2, 0.4, 0.6, 0.8, 1.0]
                
                for interval in intervals:
                    target_time = total_duration * interval
                    # Find closest timeline entry
                    closest_entry = min(timeline_data, key=lambda x: abs(x.get('timestamp', 0) - target_time))
                    
                    timestamp = closest_entry.get('timestamp', 0)
                    rep_count = closest_entry.get('rep_count', 0)
                    accuracy = closest_entry.get('accuracy_score', 0) * 100
                    
                    content.append(Paragraph(f"• {timestamp:.1f}s: Rep {rep_count}, Accuracy {accuracy:.1f}%", self.body_style))
        
        return content
    
    def _create_recommendations(self, results: Dict[str, Any]) -> List:
        """Create recommendations section"""
        content = []
        
        content.append(Paragraph("Personalized Recommendations", self.heading_style))
        
        # Generate recommendations based on analysis
        recommendations = []
        
        accuracy_score = results.get('accuracy_score', 0) * 100
        total_reps = results.get('total_reps', 0)
        correct_reps = results.get('correct_reps', 0)
        
        if accuracy_score < 70:
            recommendations.append("Focus on form quality over quantity. Consider reducing speed to maintain proper technique.")
        
        if total_reps > 0 and (correct_reps / total_reps) < 0.8:
            recommendations.append("Practice the exercise with lighter resistance or assistance to perfect your form.")
        
        mistakes = results.get('mistakes', [])
        if len(mistakes) > 5:
            recommendations.append("Consider working with a trainer to address recurring form issues.")
        
        # Exercise-specific recommendations
        exercise_name = results.get('exercise_name', '').lower()
        if 'push_up' in exercise_name:
            recommendations.append("Focus on keeping your body in a straight line and controlling the descent.")
        elif 'squat' in exercise_name:
            recommendations.append("Ensure your knees track over your toes and maintain an upright torso.")
        elif 'bicep' in exercise_name:
            recommendations.append("Keep your elbows stable at your sides and control the weight throughout the full range of motion.")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Great job! Continue practicing to maintain and improve your form.")
            recommendations.append("Consider gradually increasing intensity as your form remains consistent.")
        
        for rec in recommendations:
            content.append(Paragraph(f"• {rec}", self.body_style))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph("Generated by Workout Analyzer AI", 
                                ParagraphStyle('Footer', parent=self.styles['Normal'], 
                                             fontSize=8, textColor=colors.grey, alignment=1)))
        
        return content

# Global instance
report_generator = WorkoutReportGenerator()

async def generate_workout_report(analysis_results: Dict[str, Any]) -> BytesIO:
    """
    Generate workout analysis PDF report
    
    Args:
        analysis_results: Analysis results dictionary
        
    Returns:
        BytesIO containing the PDF report
    """
    try:
        return report_generator.generate_report(analysis_results)
    except Exception as e:
        logger.error(f"Error generating workout report: {e}")
        raise