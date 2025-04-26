import os
import cv2
import time
import numpy as np
from threading import Thread

class CameraCapture:
    """
    Camera interface for capturing document images in the voice banking system.
    Supports real-time camera preview and image capture for document processing.
    """
    
    def __init__(self, camera_id=0, image_dir="captured_images"):
        """
        Initialize the camera module.
        
        Args:
            camera_id: Camera device ID (default: 0 for primary camera)
            image_dir: Directory to save captured images
        """
        self.camera_id = camera_id
        self.camera = None
        self.image_dir = image_dir
        self.is_running = False
        self.frame = None
        
        # Create image directory if it doesn't exist
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            
        # Document frame guidelines
        self.guidelines = {
            'id_card': {
                'aspect_ratio': 1.586,  # Standard ID card ratio (85.6mm × 54mm)
                'color': (0, 255, 0)    # Green
            },
            'bank_statement': {
                'aspect_ratio': 1.414,  # A4 paper ratio
                'color': (255, 0, 0)    # Red
            },
            'payment_slip': {
                'aspect_ratio': 1.5,    # Typical payment slip ratio
                'color': (0, 0, 255)    # Blue
            }
        }
    
    def start(self):
        """
        Start the camera capture thread.
        """
        if self.is_running:
            return
            
        self.camera = cv2.VideoCapture(self.camera_id)
        
        if not self.camera.isOpened():
            raise ValueError(f"Failed to open camera with ID {self.camera_id}")
            
        # Set camera properties for document capture
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        
        self.is_running = True
        self.thread = Thread(target=self._update_frame)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """
        Stop the camera capture thread.
        """
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def _update_frame(self):
        """
        Camera update thread that continuously reads frames.
        """
        while self.is_running:
            if self.camera:
                ret, frame = self.camera.read()
                if ret:
                    self.frame = frame
            time.sleep(0.03)  # ~30 FPS
    
    def get_frame(self, document_type=None):
        """
        Get the current camera frame with optional document guidelines.
        
        Args:
            document_type: Type of document to show guidelines for
            
        Returns:
            Current camera frame with guidelines if specified
        """
        if self.frame is None:
            return None
            
        # Make a copy of the frame to avoid threading issues
        frame = self.frame.copy()
        
        # Add document guidelines if requested
        if document_type and document_type in self.guidelines:
            self._add_document_guidelines(frame, document_type)
            
        return frame
    
    def _add_document_guidelines(self, frame, document_type):
        """
        Add document guidelines overlay to the frame.
        
        Args:
            frame: Camera frame to add guidelines to
            document_type: Type of document
        """
        h, w = frame.shape[:2]
        guidelines = self.guidelines[document_type]
        
        # Calculate rectangle dimensions based on aspect ratio
        if h > w:
            # Portrait orientation
            rect_width = int(w * 0.8)
            rect_height = int(rect_width / guidelines['aspect_ratio'])
        else:
            # Landscape orientation
            rect_height = int(h * 0.8)
            rect_width = int(rect_height * guidelines['aspect_ratio'])
        
        # Calculate rectangle position (centered)
        x = (w - rect_width) // 2
        y = (h - rect_height) // 2
        
        # Draw the rectangle
        cv2.rectangle(
            frame, 
            (x, y), 
            (x + rect_width, y + rect_height), 
            guidelines['color'], 
            2
        )
        
        # Add text label
        cv2.putText(
            frame, 
            f"Align {document_type.replace('_', ' ').title()}", 
            (x, y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            guidelines['color'], 
            2
        )
    
    def capture_image(self, document_type=None, filename=None):
        """
        Capture an image for document processing.
        
        Args:
            document_type: Type of document (for metadata)
            filename: Optional custom filename
            
        Returns:
            Path to the saved image file and the image itself
        """
        if self.frame is None:
            return None, None
            
        # Make a copy of the current frame
        image = self.frame.copy()
        
        # Generate a filename if not provided
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            doc_type = document_type or "document"
            filename = f"{doc_type}_{timestamp}.jpg"
        
        # Save the image
        image_path = os.path.join(self.image_dir, filename)
        cv2.imwrite(image_path, image)
        
        return image_path, image
    
    def capture_document(self, document_type):
        """
        Specialized method to capture a document with guidelines.
        Shows preview with guidelines for 3 seconds before capturing.
        
        Args:
            document_type: Type of document to capture
            
        Returns:
            Path to captured image and the image
        """
        if not self.is_running:
            self.start()
        
        # Display guidelines for 3 seconds to help user position the document
        start_time = time.time()
        while time.time() - start_time < 3:
            frame = self.get_frame(document_type)
            
            if frame is not None:
                # Show countdown
                seconds_left = 3 - int(time.time() - start_time)
                cv2.putText(
                    frame, 
                    f"Capturing in {seconds_left}...", 
                    (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 255), 
                    2
                )
                
                cv2.imshow("Document Capture", frame)
                cv2.waitKey(1)
        
        # Capture the image
        image_path, image = self.capture_image(document_type)
        
        # Flash effect for feedback
        flash = np.ones_like(self.frame) * 255
        cv2.imshow("Document Capture", flash)
        cv2.waitKey(100)
        
        # Show the captured image for 1 second
        cv2.imshow("Document Capture", image)
        cv2.waitKey(1000)
        
        # Clean up
        cv2.destroyWindow("Document Capture")
        
        return image_path, image
