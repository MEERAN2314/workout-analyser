from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class WorkoutReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Modern color scheme (matching web app)
        self.primary_blue = colors.HexColor('#2563eb')
        self.primary_blue_light = colors.HexColor('#3b82f6')
        self.success_green = colors.HexColor('#10b981')
        self.warning_orange = colors.HexColor('#f59e0b')
        self.danger_red = colors.HexColor('#ef4444')
        self.info_blue = colors.HexColor('#3b82f6')
        self.gray_50 = colors.HexColor('#f9fafb')
        self.gray_700 = colors.HexColor('#374151')
        self.gray_900 = colors.HexColor('#111827')
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=32,
            spaceAfter=10,
            textColor=self.primary_blue,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=30,
            textColor=self.gray_700,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=15,
            spaceBefore=10,
            textColor=self.primary_blue,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=5,
            borderColor=self.primary_blue,
            leftIndent=0
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=self.gray_900,
            fontName='Helvetica-Bold'
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=self.gray_700,
            fontName='Helvetica',
            leading=16
        )
        
        self.highlight_style = ParagraphStyle(
            'Highlight',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=self.gray_900,
            fontName='Helvetica-Bold',
            backColor=self.gray_50,
            borderPadding=5
        )
    
    def generate_report(self, analysis_results: Dict[str, Any]) -> BytesIO:
        """
        Generate comprehensive PDF workout analysis report with modern styling
        
        Args:
            analysis_results: Dictionary containing analysis results
            
        Returns:
            BytesIO object containing the PDF report
        """
        try:
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create document with custom page template
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50
            )
            
            # Build story (content)
            story = []
            
            # Header with branding
            story.extend(self._create_header())
            story.append(Spacer(1, 30))
            
            # Title
            exercise_name = analysis_results.get('exercise_name', 'Unknown').replace('_', ' ').title()
            story.append(Paragraph(f"{exercise_name} Workout Analysis", self.title_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                                  self.subtitle_style))
            story.append(Spacer(1, 20))
            
            # Performance Overview Card
            story.extend(self._create_performance_card(analysis_results))
            story.append(Spacer(1, 25))
            
            # Session Information
            story.extend(self._create_session_info(analysis_results))
            story.append(Spacer(1, 25))
            
            # Detailed Metrics
            story.extend(self._create_detailed_metrics(analysis_results))
            story.append(Spacer(1, 25))
            
            # Form Feedback
            story.extend(self._create_form_feedback(analysis_results))
            story.append(Spacer(1, 25))
            
            # Mistakes and Improvements
            if analysis_results.get('mistakes'):
                story.extend(self._create_mistakes_section(analysis_results))
                story.append(Spacer(1, 25))
            
            # Timeline Summary
            if analysis_results.get('analysis_timeline'):
                story.extend(self._create_timeline_summary(analysis_results))
                story.append(Spacer(1, 25))
            
            # Recommendations
            story.extend(self._create_recommendations(analysis_results))
            story.append(Spacer(1, 30))
            
            # Footer
            story.extend(self._create_footer())
            
            # Build PDF
            doc.build(story)
            
            # Reset buffer position
            buffer.seek(0)
            
            logger.info("PDF report generated successfully")
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def _create_header(self) -> List:
        """Create modern header with branding"""
        content = []
        
        header_data = [[
            Paragraph('<font size=20 color="#2563eb"><b>💪 Workout Analyzer</b></font>', self.body_style),
            Paragraph('<font size=10 color="#6b7280">AI-Powered Fitness Analysis</font>', 
                     ParagraphStyle('HeaderRight', parent=self.body_style, alignment=TA_RIGHT))
        ]]
        
        table = Table(header_data, colWidths=[4*inch, 3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 2, self.primary_blue)
        ]))
        
        content.append(table)
        return content
    
    def _create_performance_card(self, results: Dict[str, Any]) -> List:
        """Create eye-catching performance summary card"""
        content = []
        
        # Calculate metrics
        total_reps = results.get('total_reps', 0)
        correct_reps = results.get('correct_reps', 0)
        accuracy_score = results.get('accuracy_score', 0) * 100
        calories_burned = results.get('calories_burned', 0)
        
        # Performance rating
        if accuracy_score >= 90:
            rating = "🌟 Excellent"
            rating_color = self.success_green
        elif accuracy_score >= 80:
            rating = "👍 Good"
            rating_color = self.info_blue
        elif accuracy_score >= 70:
            rating = "👌 Fair"
            rating_color = self.warning_orange
        else:
            rating = "⚠️ Needs Improvement"
            rating_color = self.danger_red
        
        # Create performance card
        card_data = [
            [Paragraph('<font size=14 color="white"><b>Performance Summary</b></font>', self.body_style), '', '', ''],
            [
                Paragraph('<font size=24 color="white"><b>{}</b></font><br/><font size=10 color="white">Total Reps</font>'.format(total_reps), 
                         ParagraphStyle('CardText', parent=self.body_style, alignment=TA_CENTER)),
                Paragraph('<font size=24 color="white"><b>{}</b></font><br/><font size=10 color="white">Correct Form</font>'.format(correct_reps), 
                         ParagraphStyle('CardText', parent=self.body_style, alignment=TA_CENTER)),
                Paragraph('<font size=24 color="white"><b>{:.1f}%</b></font><br/><font size=10 color="white">Accuracy</font>'.format(accuracy_score), 
                         ParagraphStyle('CardText', parent=self.body_style, alignment=TA_CENTER)),
                Paragraph('<font size=24 color="white"><b>{:.0f}</b></font><br/><font size=10 color="white">Calories</font>'.format(calories_burned), 
                         ParagraphStyle('CardText', parent=self.body_style, alignment=TA_CENTER))
            ],
            [Paragraph('<font size=16 color="white"><b>{}</b></font>'.format(rating), 
                      ParagraphStyle('Rating', parent=self.body_style, alignment=TA_CENTER)), '', '', '']
        ]
        
        table = Table(card_data, colWidths=[1.75*inch, 1.75*inch, 1.75*inch, 1.75*inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_blue),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            
            # Stats row
            ('BACKGROUND', (0, 1), (-1, 1), self.primary_blue_light),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, 1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, 1), 20),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 20),
            
            # Rating row
            ('BACKGROUND', (0, 2), (-1, 2), rating_color),
            ('SPAN', (0, 2), (-1, 2)),
            ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
            ('TOPPADDING', (0, 2), (-1, 2), 15),
            ('BOTTOMPADDING', (0, 2), (-1, 2), 15),
            
            # Border
            ('BOX', (0, 0), (-1, -1), 2, self.primary_blue),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.white),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.white),
        ]))
        
        content.append(table)
        return content
    
    def _create_session_info(self, results: Dict[str, Any]) -> List:
        """Create modern session information section"""
        content = []
        
        content.append(Paragraph("📋 Session Information", self.heading_style))
        content.append(Spacer(1, 10))
        
        duration = results.get('duration', 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        session_data = [
            ['Exercise Type', results.get('exercise_name', 'Unknown').replace('_', ' ').title()],
            ['Session Date', datetime.now().strftime('%B %d, %Y')],
            ['Duration', duration_str],
            ['Frames Analyzed', str(results.get('processed_frames', 0))],
            ['Analysis Quality', '✅ High' if results.get('processed_frames', 0) > 100 else '⚠️ Medium']
        ]
        
        table = Table(session_data, colWidths=[2.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.gray_50),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.gray_900),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.gray_50])
        ]))
        
        content.append(table)
        return content
    
    def _create_detailed_metrics(self, results: Dict[str, Any]) -> List:
        """Create detailed metrics section"""
        content = []
        
        content.append(Paragraph("📊 Detailed Metrics", self.heading_style))
        content.append(Spacer(1, 10))
        
        # Rep accuracy breakdown
        total_reps = results.get('total_reps', 0)
        correct_reps = results.get('correct_reps', 0)
        incorrect_reps = total_reps - correct_reps
        
        if total_reps > 0:
            rep_accuracy = (correct_reps / total_reps) * 100
            
            content.append(Paragraph("<b>Repetition Analysis:</b>", self.subheading_style))
            content.append(Paragraph(f"✅ <b>{correct_reps}</b> out of <b>{total_reps}</b> repetitions performed with correct form (<b>{rep_accuracy:.1f}%</b>)", 
                                   self.body_style))
            
            if incorrect_reps > 0:
                content.append(Paragraph(f"⚠️ <b>{incorrect_reps}</b> repetitions need form improvement", 
                                       self.body_style))
            content.append(Spacer(1, 10))
        
        # Timeline analysis
        timeline_data = results.get('analysis_timeline', [])
        if timeline_data and len(timeline_data) > 1:
            content.append(Paragraph("<b>Workout Progression:</b>", self.subheading_style))
            content.append(Paragraph(f"📈 Analysis captured <b>{len(timeline_data)}</b> key moments during your workout", 
                                   self.body_style))
            
            # Find best and worst performing moments
            best_moment = max(timeline_data, key=lambda x: x.get('accuracy_score', 0))
            worst_moment = min(timeline_data, key=lambda x: x.get('accuracy_score', 1))
            
            content.append(Paragraph(f"🌟 Best form at <b>{best_moment.get('timestamp', 0):.1f}s</b> with <b>{best_moment.get('accuracy_score', 0)*100:.1f}%</b> accuracy", 
                                   self.body_style))
            content.append(Paragraph(f"💡 Form needs attention around <b>{worst_moment.get('timestamp', 0):.1f}s</b>", 
                                   self.body_style))
        
        return content
    
    def _create_form_feedback(self, results: Dict[str, Any]) -> List:
        """Create modern form feedback section"""
        content = []
        
        feedback_list = results.get('form_feedback', [])
        if feedback_list:
            content.append(Paragraph("💬 Form Feedback", self.heading_style))
            content.append(Spacer(1, 10))
            
            # Remove duplicates
            unique_feedback = list(dict.fromkeys(feedback_list))
            
            # Create feedback items with icons
            for i, feedback in enumerate(unique_feedback[:8], 1):  # Limit to top 8
                icon = "✅" if any(word in feedback.lower() for word in ['excellent', 'good', 'great', 'perfect']) else "💡"
                content.append(Paragraph(f"{icon} {feedback}", self.body_style))
        else:
            content.append(Paragraph("💬 Form Feedback", self.heading_style))
            content.append(Spacer(1, 10))
            content.append(Paragraph("✅ No specific feedback - Keep up the good work!", self.body_style))
        
        return content
    
    def _create_mistakes_section(self, results: Dict[str, Any]) -> List:
        """Create mistakes and improvements section with modern styling"""
        content = []
        
        mistakes = results.get('mistakes', [])
        if mistakes:
            content.append(Paragraph("⚠️ Areas for Improvement", self.heading_style))
            content.append(Spacer(1, 10))
            
            # Group mistakes by severity
            high_severity = [m for m in mistakes if m.get('severity') == 'high']
            medium_severity = [m for m in mistakes if m.get('severity') == 'medium']
            low_severity = [m for m in mistakes if m.get('severity') == 'low']
            
            if high_severity:
                content.append(Paragraph("<b>🔴 High Priority Issues:</b>", self.subheading_style))
                for mistake in high_severity[:3]:
                    timestamp = mistake.get('timestamp', 0)
                    description = mistake.get('description', 'Unknown issue')
                    content.append(Paragraph(f"• At <b>{timestamp:.1f}s</b>: {description}", self.body_style))
                content.append(Spacer(1, 8))
            
            if medium_severity:
                content.append(Paragraph("<b>🟡 Medium Priority Issues:</b>", self.subheading_style))
                for mistake in medium_severity[:3]:
                    timestamp = mistake.get('timestamp', 0)
                    description = mistake.get('description', 'Unknown issue')
                    content.append(Paragraph(f"• At <b>{timestamp:.1f}s</b>: {description}", self.body_style))
                content.append(Spacer(1, 8))
            
            if low_severity:
                content.append(Paragraph("<b>🟢 Minor Issues:</b>", self.subheading_style))
                for mistake in low_severity[:2]:
                    timestamp = mistake.get('timestamp', 0)
                    description = mistake.get('description', 'Unknown issue')
                    content.append(Paragraph(f"• At <b>{timestamp:.1f}s</b>: {description}", self.body_style))
        
        return content
    
    def _create_timeline_summary(self, results: Dict[str, Any]) -> List:
        """Create timeline summary with visual progress"""
        content = []
        
        timeline_data = results.get('analysis_timeline', [])
        if len(timeline_data) > 5:
            content.append(Paragraph("⏱️ Workout Timeline Highlights", self.heading_style))
            content.append(Spacer(1, 10))
            
            # Create timeline table
            timeline_rows = [['Time', 'Rep #', 'Phase', 'Accuracy']]
            
            # Show key moments (every 20% of the workout)
            total_duration = results.get('duration', 0)
            if total_duration > 0:
                intervals = [0.2, 0.4, 0.6, 0.8, 1.0]
                
                for interval in intervals:
                    target_time = total_duration * interval
                    closest_entry = min(timeline_data, key=lambda x: abs(x.get('timestamp', 0) - target_time))
                    
                    timestamp = closest_entry.get('timestamp', 0)
                    rep_count = closest_entry.get('rep_count', 0)
                    phase = closest_entry.get('phase', 'N/A')
                    accuracy = closest_entry.get('accuracy_score', 0) * 100
                    
                    # Add emoji based on accuracy
                    accuracy_icon = "🌟" if accuracy >= 90 else "👍" if accuracy >= 80 else "👌" if accuracy >= 70 else "⚠️"
                    
                    timeline_rows.append([
                        f"{timestamp:.1f}s",
                        str(rep_count),
                        phase,
                        f"{accuracy_icon} {accuracy:.1f}%"
                    ])
                
                table = Table(timeline_rows, colWidths=[1.5*inch, 1.5*inch, 2*inch, 2*inch])
                table.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), self.primary_blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    
                    # Data rows
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.gray_50]),
                    
                    # Padding
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
                ]))
                
                content.append(table)
        
        return content
    
    def _create_recommendations(self, results: Dict[str, Any]) -> List:
        """Create personalized recommendations with modern styling"""
        content = []
        
        content.append(Paragraph("🎯 Personalized Recommendations", self.heading_style))
        content.append(Spacer(1, 10))
        
        # Generate recommendations based on analysis
        recommendations = []
        
        accuracy_score = results.get('accuracy_score', 0) * 100
        total_reps = results.get('total_reps', 0)
        correct_reps = results.get('correct_reps', 0)
        
        if accuracy_score >= 90:
            recommendations.append(("🌟", "Excellent work! Your form is outstanding. Consider increasing intensity or trying advanced variations."))
        elif accuracy_score >= 80:
            recommendations.append(("👍", "Great job! Minor adjustments will help you reach perfect form."))
        elif accuracy_score < 70:
            recommendations.append(("💪", "Focus on form quality over quantity. Consider reducing speed to maintain proper technique."))
        
        if total_reps > 0 and (correct_reps / total_reps) < 0.8:
            recommendations.append(("🎓", "Practice the exercise with lighter resistance or assistance to perfect your form."))
        
        mistakes = results.get('mistakes', [])
        if len(mistakes) > 5:
            recommendations.append(("👨‍🏫", "Consider working with a trainer to address recurring form issues."))
        
        # Exercise-specific recommendations
        exercise_name = results.get('exercise_name', '').lower()
        if 'push_up' in exercise_name:
            recommendations.append(("📐", "Focus on keeping your body in a straight line and controlling the descent."))
        elif 'squat' in exercise_name:
            recommendations.append(("🦵", "Ensure your knees track over your toes and maintain an upright torso."))
        elif 'bicep' in exercise_name:
            recommendations.append(("💪", "Keep your elbows stable at your sides and control the weight throughout the full range of motion."))
        
        # Default recommendations
        if not recommendations:
            recommendations.append(("✅", "Great job! Continue practicing to maintain and improve your form."))
            recommendations.append(("📈", "Consider gradually increasing intensity as your form remains consistent."))
        
        for icon, rec in recommendations:
            content.append(Paragraph(f"{icon} {rec}", self.body_style))
        
        return content
    
    def _create_footer(self) -> List:
        """Create modern footer"""
        content = []
        
        footer_data = [[
            Paragraph('<font size=9 color="#6b7280">Generated by <b>Workout Analyzer AI</b></font>', 
                     ParagraphStyle('FooterLeft', parent=self.body_style, alignment=TA_LEFT)),
            Paragraph(f'<font size=9 color="#6b7280">{datetime.now().strftime("%B %d, %Y")}</font>', 
                     ParagraphStyle('FooterRight', parent=self.body_style, alignment=TA_RIGHT))
        ]]
        
        table = Table(footer_data, colWidths=[4*inch, 3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        content.append(table)
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