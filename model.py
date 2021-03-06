import csv
import cv2
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Flatten, Dense, Lambda, Convolution2D, Cropping2D, Dropout
from keras.layers.pooling import MaxPooling2D

datadir = 'data/'
csvfile = datadir + 'driving_log.csv'

lines = []
with open( csvfile ) as input:
    reader = csv.reader( input )
    for line in reader:
        lines.append( line )

# The first line contains the data column's description
lines = lines[1:]

train_samples, validation_samples = train_test_split( lines, test_size=0.2 )

def generator( samples, batch_size=32 ):
    num_samples = len( samples )
    # While true, that next() can be called on the generator 
    # indefinitely over arbitrarily many epochs.
    while 1:
        sklearn.utils.shuffle( samples )
        # Loop over batches of lines read in from driving_log.csv
        for offset in range( 0, num_samples, batch_size ):
            batch_samples = samples[offset:offset+batch_size]
            # the code does not have to hold an entire array of images
            # in memory at once, the images is allocated on demand.
            # Output batches = 4*batch_size
            images = []
            angles = []
            for batch_sample in batch_samples:
                
                filename_center = batch_sample[0].split('/')[-1]
                filename_left = batch_sample[1].split('/')[-1]
                filename_right = batch_sample[2].split('/')[-1]
               
                base_IMG_Path = datadir + 'IMG/'
                path_center = base_IMG_Path + filename_center
                path_left = base_IMG_Path + filename_left
                path_right = base_IMG_Path + filename_right
                
                # Read images using mpimg. to read the image in RGB format
                image_center = mpimg.imread( path_center )
                image_left = mpimg.imread( path_left )
                image_right = mpimg.imread( path_right )

                image_flipped = np.copy( np.fliplr( image_center ) )
                
                images.append( image_center )
                images.append( image_left )
                images.append( image_right )
                images.append( image_flipped )

                # Correction angle added (subtracted)
                # to generate a driving angle for the left (right) 
                # camera images.  I tried training the network with several
                # values of this parameter. 
                correction = 0.065
                angle_center = float( batch_sample[3] )
                angle_left = angle_center + correction
                angle_right = angle_center - correction

                angle_flipped = -angle_center
                
                angles.append( angle_center )
                angles.append( angle_left ) 
                angles.append( angle_right )
                angles.append( angle_flipped )

            # Return a batch of size 4*batch_size to model.fit_generator
            X_train = np.array( images )
            y_train = np.array( angles )
           
            yield sklearn.utils.shuffle( X_train, y_train )

print( len( train_samples ) )
print( len( validation_samples ) )

train_generator = generator( train_samples, batch_size=32 )
validation_generator = generator( validation_samples, batch_size=32 )

model = Sequential()

# Crop the hood of the car and the higher parts of the images 
# which contain irrelevant sky/horizon/trees
model.add( Cropping2D( cropping=( (50,20), (0,0) ), input_shape=(160,320,3)))

model.add( Lambda( lambda x: x/255. - 0.5 ) )

# Nvidia Network
model.add( Convolution2D( 24, 5, 5, subsample=(2,2), activation = 'relu' ) )
model.add( Convolution2D( 36, 5, 5, subsample=(2,2), activation = 'relu' ) )
model.add( Convolution2D( 48, 5, 5, subsample=(2,2), activation = 'relu' ) )
model.add( Convolution2D( 64, 3, 3, subsample=(1,1), activation = 'relu' ) )
model.add( Convolution2D( 64, 3, 3, subsample=(1,1), activation = 'relu' ) )

model.add( Flatten() )

model.add( Dense( 100 ) )
model.add(Dropout(0.5)) 
model.add( Dense( 50 ) )
model.add( Dense( 10 ) )
model.add( Dense( 1 ) )

model.compile( loss='mse', optimizer='adam' )

# Define the number of times the generators of the training and validation steps will
# be called in each epoch.
#
# This should match the number of iterations in the 
# "for offset in range( 0, num_samples, batch_size ):" 
# loop of the generator.
train_steps = np.ceil( len( train_samples )/32 ).astype( np.int32 )
validation_steps = np.ceil( len( validation_samples )/32 ).astype( np.int32 )

model.fit_generator( train_generator, \
    steps_per_epoch = train_steps, \
    epochs=5, \
    verbose=1, \
    callbacks=None, 
    validation_data=validation_generator, \
    validation_steps=validation_steps, \
    class_weight=None, \
    max_q_size=10, \
    workers=1, \
    pickle_safe=False, \
    initial_epoch=0 )

model.save( 'my_model.h5' )
