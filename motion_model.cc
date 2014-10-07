#include <boost_common.h>
#include <pyarr.h>
#include <cmath>

#include <boost/math/distributions/normal.hpp>
#include <boost/random.hpp>

#include "motion_model.h"

using std::cout;
using std::endl;


boost::random::normal_distribution<> normal_dist(0, 1);

boost::random::mt19937 rng;

boost::variate_generator<boost::mt19937&, 
			     boost::normal_distribution<> > normal_generator(rng, normal_dist);

void motion_model::compute_relative_transform(pyarr<double> &pose,
				pyarr<double> &u,
				float u_norm,
				float u_arctan,
				double &drot1,
				double &dtrans,
				double &drot2)
{
    drot1 = u_arctan - pose[ind(2)];
    dtrans = (double)u_norm;
    drot2 = u[ind(2)] - drot1;
}

vector<double> motion_model::update_pose_with_sample(pyarr<double> &pose,
						    vector<double> &sample)
{
    vector<double> new_pose(3, 0);
    
    new_pose[0] = pose[ind(0)] + sample[1] * cos(pose[ind(2)] + sample[0]);
    new_pose[1] = pose[ind(1)] + sample[1] * sin(pose[ind(2)] + sample[0]);
    new_pose[2] = true_mod((pose[ind(2)] + sample[0] + sample[2]), 2*M_PI);
    return new_pose;
}


pyarr<double> motion_model::update(pyarr<double> pose, 
				   pyarr<double> u,
				   float u_norm,
				   float u_arctan)
{
    double drot1, dtrans, drot2;
    
    compute_relative_transform(pose,
			       u,
			       u_norm,
			       u_arctan,
			       drot1,
			       dtrans,
			       drot2);
    
    double drot1_sq = pow(drot1, 2);
    double dtrans_sq = pow(dtrans, 2);
    double drot2_sq = pow(drot2, 2);

    double num = normal_generator();

    vector<double> sample;
    
    sample.push_back(drot1 + (alpha1 * drot1_sq + alpha2 * dtrans_sq) * normal_generator());
    sample.push_back(dtrans + (alpha3 * dtrans_sq + alpha4 * drot1_sq + alpha4 * drot2_sq) * normal_generator());
    sample.push_back(drot2 + (alpha1 * drot2_sq + alpha2 * dtrans_sq) * normal_generator());

    vector<long int> dims;
    dims.push_back(3);
    pyarr<double> new_pose(dims);

    vector<double> new_pose_vec = update_pose_with_sample(pose, sample);
    new_pose[ind(0)] = new_pose_vec[0];
    new_pose[ind(1)] = new_pose_vec[1];
    new_pose[ind(2)] = new_pose_vec[2];
    return new_pose;
}

BOOST_PYTHON_MODULE(libmotion_model)
{
    import_array();
    boost_common();
    
    class_<motion_model>("motion_model", init<>())
	.def("update", &motion_model::update)
	;
}